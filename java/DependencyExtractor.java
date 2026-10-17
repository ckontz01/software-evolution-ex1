import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.jar.*;
import java.util.zip.*;
import org.objectweb.asm.*;
import org.objectweb.asm.signature.*;

/** Supplemental static bytecode evidence extractor. Never executes targets.
 * Supplies class ownership/enclosing metadata and member identities for UE.
 * Its broad relationship model is saved only as supplemental_dependencies*;
 * the course instructor's unmodified JAR supplies the primary graph.
 * Member identities preserve their original declaring binary owners even when
 * canonical class nodes are merged to their outermost owned class.
 */
public final class DependencyExtractor {
    static final int API = Opcodes.ASM9;
    static final Map<String, Info> infos = new TreeMap<>();
    static final Map<String, String> parent = new HashMap<>();
    static final Set<String> sourcePaths = new HashSet<>();
    static final Set<String> typed = new TreeSet<>();
    static final Set<String> members = new TreeSet<>();
    static final Map<String, Integer> excludedEdges = new TreeMap<>();
    // HashMap containsKey distinguishes a memoized unresolved lookup from a miss.
    static final Map<String, String> resolvedMembers = new HashMap<>();
    static final List<String[]> unresolved = new ArrayList<>();
    static long seenClassRelations = 0, seenMemberUses = 0;
    static long resolutionCacheHits = 0, interfaceResolutionTies = 0;

    static final class Info {
        String name, superName, source;
        String[] interfaces;
        int access;
        byte[] bytes;
        final Set<String> methods = new HashSet<>(), fields = new HashSet<>();
        final Map<String, Integer> methodAccess = new HashMap<>();
        boolean included;
        String exclusion = "";
    }
    static String display(String name) { return name.replace('/', '.'); }
    static String outer(String name) {
        Set<String> visited = new HashSet<>();
        while (parent.containsKey(name)) {
            if (!visited.add(name)) throw new IllegalStateException("Cyclic enclosing metadata: " + name);
            name = parent.get(name);
        }
        return name;
    }
    static String member(String owner, String kind, String name, String desc) {
        return display(owner) + "#" + kind + ":" + name + desc;
    }
    static void excluded(String reason) { excludedEdges.merge(reason, 1, Integer::sum); }
    static boolean included(String name) { return infos.containsKey(name) && infos.get(name).included; }
    static void relation(String source, String target, String kind) {
        if (target == null) return;
        if (target.startsWith("[")) { type(source, Type.getType(target), kind); return; }
        seenClassRelations++;
        if (!included(source) || !included(target)) { excluded("out_of_scope_target"); return; }
        String a = outer(source), b = outer(target);
        if (a.equals(b)) { excluded("self_after_outer_merge"); return; }
        typed.add(display(a) + "\t" + display(b) + "\t" + kind);
    }
    static void type(String owner, Type t, String kind) {
        if (t.getSort() == Type.OBJECT) relation(owner, t.getInternalName(), kind);
        else if (t.getSort() == Type.ARRAY) type(owner, t.getElementType(), kind);
        else if (t.getSort() == Type.METHOD) {
            for (Type a : t.getArgumentTypes()) type(owner, a, "METHOD_PARAMETER");
            type(owner, t.getReturnType(), "TYPE_USAGE");
        }
    }
    static void signature(String owner, String signature, boolean fieldType) {
        if (signature == null) return;
        SignatureVisitor v = signatureVisitor(owner);
        if (fieldType) new SignatureReader(signature).acceptType(v);
        else new SignatureReader(signature).accept(v);
    }
    static SignatureVisitor signatureVisitor(String owner) {
        return new SignatureVisitor(API) {
            String current;
            public void visitClassType(String name) { current = name; relation(owner, name, "TYPE_USAGE"); }
            public void visitInnerClassType(String name) {
                if (current == null) throw new IllegalArgumentException("Inner type without its outer signature");
                current = current + "$" + name;
                relation(owner, current, "TYPE_USAGE");
            }
            // A type argument must not overwrite its enclosing type's current
            // owner: Outer<Arg>.Inner<Result> names Outer$Inner, not Arg$Inner.
            public SignatureVisitor visitTypeArgument(char wildcard) { return signatureVisitor(owner); }
            public SignatureVisitor visitArrayType() { return signatureVisitor(owner); }
            public SignatureVisitor visitClassBound() { return signatureVisitor(owner); }
            public SignatureVisitor visitInterfaceBound() { return signatureVisitor(owner); }
            public SignatureVisitor visitSuperclass() { return signatureVisitor(owner); }
            public SignatureVisitor visitInterface() { return signatureVisitor(owner); }
            public SignatureVisitor visitParameterType() { return signatureVisitor(owner); }
            public SignatureVisitor visitReturnType() { return signatureVisitor(owner); }
            public SignatureVisitor visitExceptionType() { return signatureVisitor(owner); }
        };
    }
    static AnnotationVisitor annotation(String owner, String desc) {
        type(owner, Type.getType(desc), "TYPE_USAGE");
        return new AnnotationVisitor(API) {
            public void visit(String name, Object value) {
                if (value instanceof Type) type(owner, (Type)value, "TYPE_USAGE");
            }
            public void visitEnum(String name, String descriptor, String value) {
                type(owner, Type.getType(descriptor), "TYPE_USAGE");
            }
            public AnnotationVisitor visitAnnotation(String name, String descriptor) {
                return annotation(owner, descriptor);
            }
            public AnnotationVisitor visitArray(String name) { return this; }
        };
    }

    /** Resolve a declared member using available artifact metadata. Field lookup
     * and method lookup deliberately have different orders (JVMS 5.4.3.2--4).
     * Constructors are never inherited. Unavailable library declarations and
     * dynamic receiver dispatch remain outside this static evidence model.
     */
    static String resolve(String owner, String name, String desc, boolean isField) {
        String cacheKey = (isField ? "F\t" : "M\t") + owner + "\t" + name + "\t" + desc;
        if (resolvedMembers.containsKey(cacheKey)) {
            resolutionCacheHits++;
            return resolvedMembers.get(cacheKey);
        }
        String resolved = isField
                ? resolveField(owner, name + desc, new HashSet<>())
                : resolveMethod(owner, name, desc);
        resolvedMembers.put(cacheKey, resolved);
        return resolved;
    }
    static String resolveField(String owner, String key, Set<String> visited) {
        if (owner == null || !visited.add(owner)) return null;
        Info info = infos.get(owner);
        if (info == null) return null;
        if (info.fields.contains(key)) return owner;
        // JVMS: own declaration, recursively direct interfaces, then superclass.
        for (String it : info.interfaces) {
            String resolved = resolveField(it, key, visited);
            if (resolved != null) return resolved;
        }
        return resolveField(info.superName, key, visited);
    }
    static void collectInterfaces(String owner, Set<String> found) {
        Info info = infos.get(owner);
        if (info == null) return;
        for (String it : info.interfaces) if (found.add(it)) collectInterfaces(it, found);
    }
    static boolean isSuperInterface(String possibleSuper, String possibleSub) {
        Set<String> ancestors = new HashSet<>();
        collectInterfaces(possibleSub, ancestors);
        return ancestors.contains(possibleSuper);
    }
    static String resolveMethod(String owner, String name, String desc) {
        Info initial = infos.get(owner);
        if (initial == null) return null;
        String key = name + desc;
        if (name.equals("<init>") || name.equals("<clinit>"))
            return initial.methods.contains(key) ? owner : null;
        Set<String> visited = new HashSet<>();
        Set<String> interfaces = new TreeSet<>();
        // Every class in the superclass chain precedes every superinterface.
        // For an interface this checks its own declaration; Object metadata is
        // normally outside the artifact, so missing Object methods stay unknown.
        for (String current = owner; current != null && visited.add(current);) {
            Info info = infos.get(current);
            if (info == null) break;
            if (info.methods.contains(key)) return current;
            collectInterfaces(current, interfaces);
            current = info.superName;
        }
        List<String> candidates = new ArrayList<>();
        for (String it : interfaces) {
            Info info = infos.get(it);
            if (info == null) continue;
            Integer access = info.methodAccess.get(key);
            if (access != null && (access & (Opcodes.ACC_PRIVATE | Opcodes.ACC_STATIC)) == 0)
                candidates.add(it);
        }
        if (candidates.isEmpty()) return null;
        List<String> concreteMaximal = new ArrayList<>();
        for (String candidate : candidates) {
            if ((infos.get(candidate).methodAccess.get(key) & Opcodes.ACC_ABSTRACT) != 0) continue;
            boolean shadowed = false;
            for (String other : candidates)
                if (!other.equals(candidate) && isSuperInterface(candidate, other)) { shadowed = true; break; }
            if (!shadowed) concreteMaximal.add(candidate);
        }
        if (concreteMaximal.size() == 1) return concreteMaximal.get(0);
        // JVMS permits an arbitrary eligible interface declaration in this case.
        // A lexical choice makes static results reproducible and is counted.
        if (candidates.size() > 1) interfaceResolutionTies++;
        return candidates.get(0);
    }
    static void use(String sourceOwner, String sourceMember, String targetOwner,
                    String name, String desc, boolean field) {
        seenMemberUses++;
        String kind = field ? "FIELD_REFERENCE" : "METHOD_CALL";
        String resolved = resolve(targetOwner, name, desc, field);
        // Keep the symbolic dependency when no internal declaration is available;
        // UE receives only resolved genuine member evidence.
        relation(sourceOwner, resolved == null ? targetOwner : resolved, kind);
        if (resolved == null) {
            if (included(targetOwner)) unresolved.add(new String[]{display(sourceOwner), sourceMember,
                    display(targetOwner), name + desc, kind});
            return;
        }
        if (!included(sourceOwner) || !included(resolved)) return;
        String a = outer(sourceOwner), b = outer(resolved);
        if (a.equals(b)) return;
        members.add(display(a) + "\t" + sourceMember + "\t" + display(b) + "\t"
                + member(resolved, field ? "F" : "M", name, desc));
    }
    static void handle(String owner, String sourceMember, Handle h) {
        int tag = h.getTag();
        boolean field = tag >= Opcodes.H_GETFIELD && tag <= Opcodes.H_PUTSTATIC;
        use(owner, sourceMember, h.getOwner(), h.getName(), h.getDesc(), field);
        type(owner, field ? Type.getType(h.getDesc()) : Type.getMethodType(h.getDesc()), "TYPE_USAGE");
    }
    static void constant(String owner, String sourceMember, Object value) {
        if (value instanceof Type) type(owner, (Type)value, "TYPE_USAGE");
        else if (value instanceof Handle) handle(owner, sourceMember, (Handle)value);
        else if (value instanceof ConstantDynamic) {
            ConstantDynamic c = (ConstantDynamic)value;
            type(owner, Type.getType(c.getDescriptor()), "TYPE_USAGE");
            handle(owner, sourceMember, c.getBootstrapMethod());
            for (int j = 0; j < c.getBootstrapMethodArgumentCount(); j++)
                constant(owner, sourceMember, c.getBootstrapMethodArgument(j));
        }
    }
    static void scan(Info info) {
        final String owner = info.name;
        new ClassReader(info.bytes).accept(new ClassVisitor(API) {
            public void visit(int version, int access, String name, String sig,
                              String superName, String[] interfaces) {
                relation(owner, superName, "EXTENDS");
                for (String it : interfaces) relation(owner, it,
                        (access & Opcodes.ACC_INTERFACE) != 0 ? "EXTENDS" : "IMPLEMENTS");
                signature(owner, sig, false);
            }
            public AnnotationVisitor visitAnnotation(String desc, boolean visible) { return annotation(owner, desc); }
            public AnnotationVisitor visitTypeAnnotation(int ref, TypePath path, String desc, boolean visible) {
                return annotation(owner, desc);
            }
            public FieldVisitor visitField(int access, String name, String desc, String sig, Object value) {
                type(owner, Type.getType(desc), "TYPE_USAGE");
                signature(owner, sig, true);
                return new FieldVisitor(API) {
                    public AnnotationVisitor visitAnnotation(String d, boolean v) { return annotation(owner, d); }
                    public AnnotationVisitor visitTypeAnnotation(int r, TypePath p, String d, boolean v) {
                        return annotation(owner, d);
                    }
                };
            }
            public MethodVisitor visitMethod(int access, String name, String desc, String sig, String[] exceptions) {
                final String sourceMember = member(owner, "M", name, desc);
                type(owner, Type.getMethodType(desc), "TYPE_USAGE");
                signature(owner, sig, false);
                if (exceptions != null) for (String ex : exceptions) relation(owner, ex, "EXCEPTION_THROWS");
                return new MethodVisitor(API) {
                    public AnnotationVisitor visitAnnotation(String d, boolean v) { return annotation(owner, d); }
                    public AnnotationVisitor visitParameterAnnotation(int p, String d, boolean v) { return annotation(owner, d); }
                    public AnnotationVisitor visitTypeAnnotation(int r, TypePath p, String d, boolean v) {
                        return annotation(owner, d);
                    }
                    public void visitTypeInsn(int opcode, String target) { relation(owner, target, "TYPE_USAGE"); }
                    public void visitFieldInsn(int opcode, String target, String name, String d) {
                        use(owner, sourceMember, target, name, d, true);
                        type(owner, Type.getType(d), "TYPE_USAGE");
                    }
                    public void visitMethodInsn(int opcode, String target, String name, String d, boolean itf) {
                        use(owner, sourceMember, target, name, d, false);
                        type(owner, Type.getMethodType(d), "TYPE_USAGE");
                    }
                    public void visitInvokeDynamicInsn(String name, String d, Handle bootstrap, Object... args) {
                        type(owner, Type.getMethodType(d), "TYPE_USAGE");
                        handle(owner, sourceMember, bootstrap);
                        for (Object arg : args) constant(owner, sourceMember, arg);
                    }
                    public void visitLdcInsn(Object value) { constant(owner, sourceMember, value); }
                    public void visitMultiANewArrayInsn(String d, int dims) { type(owner, Type.getType(d), "TYPE_USAGE"); }
                    public void visitTryCatchBlock(Label start, Label end, Label handler, String target) {
                        if (target != null) relation(owner, target, "TYPE_USAGE");
                    }
                };
            }
        }, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
    }
    static void csv(Path path, String[] header, Iterable<String[]> rows) throws IOException {
        try (BufferedWriter w = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
            writeCsv(w, header);
            for (String[] row : rows) writeCsv(w, row);
        }
    }
    static void writeCsv(BufferedWriter w, String[] row) throws IOException {
        for (int j = 0; j < row.length; j++) {
            if (j > 0) w.write(',');
            w.write('"'); w.write(row[j].replace("\"", "\"\"")); w.write('"');
        }
        w.newLine();
    }
    static List<String[]> splitRows(Set<String> rows) {
        List<String[]> result = new ArrayList<>();
        for (String r : rows) result.add(r.split("\t", -1));
        return result;
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) {
            System.err.println("Usage: DependencyExtractor binary.jar sources.jar output-directory package.prefix[,package.prefix...]");
            System.exit(2);
        }
        Path output = Paths.get(args[2]); Files.createDirectories(output);
        List<String> prefixes = new ArrayList<>();
        for (String value : args[3].split(",", -1)) {
            String valueTrimmed = value.trim();
            if (valueTrimmed.isEmpty()) throw new IllegalArgumentException("Empty owned namespace");
            prefixes.add(valueTrimmed.replace('.', '/') + "/");
        }
        try (ZipFile z = new ZipFile(args[1])) {
            Enumeration<? extends ZipEntry> entries = z.entries();
            while (entries.hasMoreElements()) {
                String n = entries.nextElement().getName();
                if (n.endsWith(".java")) sourcePaths.add(n);
            }
        }
        int mrSkipped = 0, metadataSkipped = 0;
        try (JarFile jar = new JarFile(args[0])) {
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry e = entries.nextElement(); String entry = e.getName();
                if (!entry.endsWith(".class")) continue;
                if (entry.startsWith("META-INF/versions/")) { mrSkipped++; continue; }
                if (entry.endsWith("module-info.class") || entry.endsWith("package-info.class")) {
                    metadataSkipped++; continue;
                }
                Info i = new Info();
                try (InputStream in = jar.getInputStream(e)) { i.bytes = in.readAllBytes(); }
                new ClassReader(i.bytes).accept(new ClassVisitor(API) {
                    public void visit(int v, int a, String n, String sig, String sup, String[] itfs) {
                        i.name=n; i.access=a; i.superName=sup; i.interfaces=itfs;
                    }
                    public void visitSource(String s, String debug) { i.source=s; }
                    public void visitOuterClass(String owner, String n, String desc) { parent.put(i.name,owner); }
                    public void visitInnerClass(String n, String out, String inner, int a) {
                        if (out != null) parent.put(n,out);
                    }
                    public FieldVisitor visitField(int a, String n, String d, String s, Object v) {
                        i.fields.add(n+d); return null;
                    }
                    public MethodVisitor visitMethod(int a, String n, String d, String s, String[] ex) {
                        i.methods.add(n+d); i.methodAccess.put(n+d,a); return null;
                    }
                }, ClassReader.SKIP_CODE | ClassReader.SKIP_FRAMES);
                if (infos.put(i.name,i) != null) throw new IllegalArgumentException("Duplicate class: "+i.name);
            }
        }
        for (Info i : infos.values()) {
            String file = i.source == null ? outer(i.name).substring(outer(i.name).lastIndexOf('/')+1)+".java" : i.source;
            String path = i.name.substring(0,i.name.lastIndexOf('/')+1)+file;
            boolean ownedNamespace = false;
            for (String prefix : prefixes) if (i.name.startsWith(prefix)) ownedNamespace = true;
            if (!ownedNamespace) i.exclusion="outside_project_namespace";
            else if (i.name.contains("/internal/shaded/") || i.name.contains("/io/doubleparser/")) i.exclusion="shaded_third_party";
            else if (!sourcePaths.contains(path)) i.exclusion="no_owned_source_file";
            else { i.included=true; i.source=path; }
        }
        // Reject rather than silently invent an enclosing top-level class.
        for (Info i : infos.values()) if (i.included && !included(outer(i.name))) {
            i.included=false; i.exclusion="enclosing_class_not_owned";
        }
        for (Info i : infos.values()) if (i.included) scan(i);
        Map<String,List<Info>> groups=new TreeMap<>();
        List<String[]> aliases=new ArrayList<>(), rejected=new ArrayList<>();
        for (Info i : infos.values()) {
            if (i.included) {
                String o=outer(i.name); groups.computeIfAbsent(o,k->new ArrayList<>()).add(i);
                aliases.add(new String[]{display(i.name),display(o),i.source});
            } else rejected.add(new String[]{display(i.name),i.exclusion});
        }
        List<String[]> classes=new ArrayList<>();
        for (Map.Entry<String,List<Info>> e : groups.entrySet()) {
            Info i=infos.get(e.getKey());
            String kind=(i.access&Opcodes.ACC_ANNOTATION)!=0?"annotation":(i.access&Opcodes.ACC_INTERFACE)!=0?"interface":
                    (i.access&Opcodes.ACC_ENUM)!=0?"enum":(i.access&Opcodes.ACC_RECORD)!=0?"record":"class";
            classes.add(new String[]{display(i.name),display(i.name.substring(0,i.name.lastIndexOf('/'))),
                    i.source,kind,Integer.toString(e.getValue().size())});
        }
        csv(output.resolve("classes.csv"),new String[]{"class","package","source_file","kind","raw_binary_classes"},classes);
        csv(output.resolve("class_aliases.csv"),new String[]{"binary_class","class","source_file"},aliases);
        csv(output.resolve("excluded_classes.csv"),new String[]{"binary_class","reason"},rejected);
        csv(output.resolve("supplemental_dependencies_typed.csv"),new String[]{"source","target","relation"},splitRows(typed));
        csv(output.resolve("member_dependencies.csv"),new String[]{"source_class","source_member","target_class","target_member"},splitRows(members));
        csv(output.resolve("unresolved_member_uses.csv"),new String[]{"source_class","source_member","symbolic_target","member","relation"},unresolved);
        Set<String> edges=new TreeSet<>();
        for (String row:typed) { String[] cols=row.split("\t");edges.add(cols[0]+"\t"+cols[1]); }
        csv(output.resolve("supplemental_dependencies.csv"),new String[]{"source","target"},splitRows(edges));
        List<String[]> stats=new ArrayList<>();
        stats.add(new String[]{"canonical_classes",Integer.toString(classes.size())});
        stats.add(new String[]{"owned_binary_classes",Integer.toString(aliases.size())});
        stats.add(new String[]{"excluded_binary_classes",Integer.toString(rejected.size())});
        stats.add(new String[]{"multi_release_class_entries_excluded",Integer.toString(mrSkipped)});
        stats.add(new String[]{"metadata_class_entries_excluded",Integer.toString(metadataSkipped)});
        stats.add(new String[]{"unique_directed_edges",Integer.toString(edges.size())});
        stats.add(new String[]{"unique_typed_edges",Integer.toString(typed.size())});
        stats.add(new String[]{"unique_member_edges",Integer.toString(members.size())});
        stats.add(new String[]{"observed_class_relation_events",Long.toString(seenClassRelations)});
        stats.add(new String[]{"observed_member_use_events",Long.toString(seenMemberUses)});
        stats.add(new String[]{"member_resolution_cache_entries",Integer.toString(resolvedMembers.size())});
        stats.add(new String[]{"member_resolution_cache_hits",Long.toString(resolutionCacheHits)});
        stats.add(new String[]{"interface_resolution_ties",Long.toString(interfaceResolutionTies)});
        for (Map.Entry<String,Integer> e:excludedEdges.entrySet())stats.add(new String[]{e.getKey(),e.getValue().toString()});
        csv(output.resolve("supplemental_extraction_counts.csv"),new String[]{"metric","value"},stats);
        System.out.println("classes="+classes.size()+" supplemental_dependencies="+edges.size()+" member_edges="+members.size());
    }
}
