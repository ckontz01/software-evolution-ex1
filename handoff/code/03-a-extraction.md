# Commit 03 — Instructor extraction and complete Java toolchain

**Student A · 2026-10-19 · 37 complete files · 25 full code/configuration listings**

Source snapshot: `a8186f58fb22ffd7ebbe68964ded49006f12aef4`. Dates are planned work sessions; make the commit when you actually import and review this packet.

## What to understand

Trace one real call, field, inheritance and inner/anonymous-class reference. Distinguish the instructor graph from supplemental ownership/member evidence.

## Apply this packet

Set `HANDOFF_DIR` to your extracted student bundle and `TEACHER_REPO` to the teacher checkout. Pull the preceding commit first. Commands below use the `guava-study` layout explained in the main map.

```bash
git -C "$TEACHER_REPO" pull --ff-only origin guava-assignment
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/03-a-extraction" --target "$TEACHER_REPO" --subdir guava-study
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/03-a-extraction" --target "$TEACHER_REPO" --subdir guava-study --apply
cd "$TEACHER_REPO/guava-study"
```

For commit 01, create the shared branch as shown in the main map; its remote branch does not exist until the first push, so omit that first pull.

## Checks before the commit

Run these in the cumulative study directory after applying the packet. For packet 01, first create the Python environment and install the locked requirements as shown in the main map:

```bash
python scripts/fetch_tools.py
python scripts/build_java.py
PYTHONPATH=src python -m unittest discover -s tests -p 'test_extractor.py' -v
```

Stage and inspect only this packet, then use your own Git identity:

```bash
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/03-a-extraction" --target "$TEACHER_REPO" --subdir guava-study --apply --stage
git -C "$TEACHER_REPO" diff --cached --stat
git -C "$TEACHER_REPO" diff --cached
python "$HANDOFF_DIR/apply_packet.py" --packet "$HANDOFF_DIR/packets/03-a-extraction" --target "$TEACHER_REPO" --subdir guava-study --check-staged
git -C "$TEACHER_REPO" commit -m 'import: add instructor extraction and complete Java toolchain (AI-assisted preparation)'
git -C "$TEACHER_REPO" push -u origin guava-assignment
```

Add a commit-message paragraph describing the checks you actually performed and anything you found. The import message identifies the prepared source; it does not claim you originally wrote every line.

## Every file to push

All files below are present under this packet's `payload/` directory in the complete student download. Paths are relative to the study directory.

| File | Bytes | Content |
|---|---:|---|
| `THIRD_PARTY.md` | 1,698 | documentation or tool provenance |
| `docs/modeling_decisions.md` | 13,753 | documentation or tool provenance |
| `java/DependencyExtractor.java` | 24,697 | Full code below |
| `scripts/build_java.py` | 535 | Full code below |
| `scripts/fetch_tools.py` | 1,602 | Full code below |
| `scripts/run_checks.py` | 558 | Full code below |
| `src/evolution/extraction.py` | 18,206 | Full code below |
| `src/evolution/toolchain.py` | 5,560 | Full code below |
| `tests/test_extractor.py` | 18,273 | Full code below |
| `third_party/acdc/README` | 147 | documentation or tool provenance |
| `third_party/acdc/UPSTREAM.md` | 1,573 | documentation or tool provenance |
| `third_party/acdc/acdc.tar` | 163,840 | binary archive payload |
| `third_party/acdc/acdc/ACDC.java` | 10,378 | Full code below |
| `third_party/acdc/acdc/BodyHeader.java` | 7,194 | Full code below |
| `third_party/acdc/acdc/ClusterLast.java` | 2,134 | Full code below |
| `third_party/acdc/acdc/DownInducer.java` | 1,165 | Full code below |
| `third_party/acdc/acdc/Edge.java` | 3,413 | Full code below |
| `third_party/acdc/acdc/FullOutput.java` | 819 | Full code below |
| `third_party/acdc/acdc/IO.java` | 582 | Full code below |
| `third_party/acdc/acdc/Inducer.java` | 149 | Full code below |
| `third_party/acdc/acdc/InputHandler.java` | 172 | Full code below |
| `third_party/acdc/acdc/Node.java` | 6,729 | Full code below |
| `third_party/acdc/acdc/OrphanAdoption.java` | 15,040 | Full code below |
| `third_party/acdc/acdc/OutputHandler.java` | 172 | Full code below |
| `third_party/acdc/acdc/Pattern.java` | 4,329 | Full code below |
| `third_party/acdc/acdc/RSFOutput.java` | 1,222 | Full code below |
| `third_party/acdc/acdc/Sortable.java` | 840 | Full code below |
| `third_party/acdc/acdc/SubGraph.java` | 12,055 | Full code below |
| `third_party/acdc/acdc/TAInput.java` | 11,256 | Full code below |
| `third_party/acdc/acdc/UpInducer.java` | 905 | Full code below |
| `third_party/acdc/download.json` | 207 | documentation or tool provenance |
| `third_party/acdc/source_sha256.json` | 1,745 | documentation or tool provenance |
| `third_party/dependency_extractor/DependencyExtractor.jar` | 2,671,409 | bundled java tool |
| `third_party/dependency_extractor/UPSTREAM.md` | 3,002 | documentation or tool provenance |
| `third_party/dependency_extractor/source.json` | 1,246 | documentation or tool provenance |
| `tools/asm-9.7.1.jar` | 126,093 | bundled java tool |
| `tools/ecj-3.37.0.jar` | 3,257,207 | bundled java tool |

The machine-readable `packet.json` pins every file's SHA-256 and Git blob. Binary JAR/PDF/ZIP files and large evidence files are supplied as their exact original bytes in the payload, rather than as text pasted into this guide.

## Whole code

The following are complete files, with no omitted functions. Use the payload for copying so file bytes, line endings and original licences stay intact.

The official ACDC Java files below retain their upstream authorship. The instructor supplied DependencyExtractor as a compiled JAR; that original JAR is included in full, and unavailable instructor source is not invented. `java/DependencyExtractor.java` is our supplemental extractor.

### java/DependencyExtractor.java

SHA-256: `c59e60ce2e713deb4eae0547b6d4a61ad3af281d9f31a7cf2b47eaa3bbb14b94` · 24,697 bytes

<!-- FULL_SOURCE java/DependencyExtractor.java c59e60ce2e713deb4eae0547b6d4a61ad3af281d9f31a7cf2b47eaa3bbb14b94 -->
```java
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
```
<!-- END_FULL_SOURCE java/DependencyExtractor.java -->

### scripts/build_java.py

SHA-256: `d0d1d0789f860992159c1371b3806a5f5732fc96faed59754cc16b6de9be9ce7` · 535 bytes

<!-- FULL_SOURCE scripts/build_java.py d0d1d0789f860992159c1371b3806a5f5732fc96faed59754cc16b6de9be9ce7 -->
```python
#!/usr/bin/env python3
"""Compile the extractor and the unmodified official ACDC sources."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from evolution.toolchain import build_java

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java", help="Java 17+ executable; optional when java is on PATH")
    args = parser.parse_args()
    print(json.dumps(build_java(args.java), indent=2))
```
<!-- END_FULL_SOURCE scripts/build_java.py -->

### scripts/fetch_tools.py

SHA-256: `fbb3c97bff87420af6503586c81728f5fe00140400a09666583685b3ed1245f7` · 1,602 bytes

<!-- FULL_SOURCE scripts/fetch_tools.py fbb3c97bff87420af6503586c81728f5fe00140400a09666583685b3ed1245f7 -->
```python
#!/usr/bin/env python3
"""Verify pinned tools, fetching public ASM/ECJ only when absent.

The instructor JAR is bundled unchanged and its nested analysis dependencies
are extracted locally for the portable classpath launcher. These libraries are
analysis tools; they never become nodes in the target Guava graph.
"""
from pathlib import Path
import hashlib
import urllib.request
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from evolution.toolchain import instructor_classpath
ARTIFACTS = [
    ("asm-9.7.1.jar", "org/ow2/asm/asm/9.7.1/asm-9.7.1.jar", "8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281"),
    ("ecj-3.37.0.jar", "org/eclipse/jdt/ecj/3.37.0/ecj-3.37.0.jar", "cde026ff966b48b5e5f148b6f041ceff3cf4f85cf75155f4ec0f40e4ee14b545"),
]

if __name__ == "__main__":
    (ROOT / "tools").mkdir(exist_ok=True)
    for filename, suffix, expected in ARTIFACTS:
        target = ROOT / "tools" / filename
        if not target.exists():
            with urllib.request.urlopen("https://repo.maven.apache.org/maven2/" + suffix, timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError(f"Checksum mismatch: {filename}")
            target.write_bytes(content)
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {filename}")
        print("verified", filename)
    for path in instructor_classpath():
        print("verified", path.relative_to(ROOT).as_posix())
```
<!-- END_FULL_SOURCE scripts/fetch_tools.py -->

### scripts/run_checks.py

SHA-256: `74082810dc5f9b7199cefee6dc1cfcd0a6f698516a195a49ae9994b4198a7436` · 558 bytes

<!-- FULL_SOURCE scripts/run_checks.py 74082810dc5f9b7199cefee6dc1cfcd0a6f698516a195a49ae9994b4198a7436 -->
```python
#!/usr/bin/env python3
"""Build the real Java tools and execute the focused correctness tests."""
import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from evolution.toolchain import build_java

if __name__ == '__main__':
    build_java()
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
```
<!-- END_FULL_SOURCE scripts/run_checks.py -->

### src/evolution/extraction.py

SHA-256: `6f9c82fbff5030be0cba95a40763764f5e2a55e5c34ad2c62fd3adf9b4932923` · 18,206 bytes

<!-- FULL_SOURCE src/evolution/extraction.py 6f9c82fbff5030be0cba95a40763764f5e2a55e5c34ad2c62fd3adf9b4932923 -->
```python
"""Instructor class graphs plus separate member-aware supplemental evidence.

Only the unmodified instructor tool contributes primary graph relationships.
The custom ASM pass supplies source ownership, enclosing identities and UE
member evidence; its broader graph is preserved for sensitivity auditing only.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import os
from pathlib import Path
import subprocess
import time
import zipfile

from .graph import read_csv, read_graph, sha256, write_csv, write_json
from .toolchain import (ROOT, INSTRUCTOR_JAR, INSTRUCTOR_SHA256,
                        instructor_classpath, java_env, java_path)


def count_java_lines(text: str) -> dict[str, int]:
    """Count physical/nonblank/code lines with a small Java comment/string lexer.

    This is a size indicator, not a measure of functionality. Text blocks are
    respected. A line containing both code and a comment counts as a code line.
    """
    lines = text.splitlines()
    state = "code"
    code_count = 0
    for line in lines:
        i, has_code = 0, False
        while i < len(line):
            if state == "block":
                end = line.find("*/", i)
                if end < 0:
                    break
                state, i = "code", end + 2
            elif state == "text":
                has_code = True
                end = line.find('"""', i)
                if end < 0:
                    break
                state, i = "code", end + 3
            elif line.startswith("//", i):
                break
            elif line.startswith("/*", i):
                state, i = "block", i + 2
            elif line.startswith('"""', i):
                has_code, state, i = True, "text", i + 3
            elif line[i] in "\"'":
                has_code, quote, i = True, line[i], i + 1
                while i < len(line):
                    if line[i] == "\\":
                        i += 2
                    elif line[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
            else:
                has_code = has_code or not line[i].isspace()
                i += 1
        code_count += int(has_code)
    return {"physical_java_lines": len(lines), "nonblank_java_lines": sum(bool(x.strip()) for x in lines), "java_code_lines": code_count}



OWNED_PREFIXES = ("com.google.common", "com.google.thirdparty.publicsuffix")
RELATIONS = frozenset({"EXTENDS", "IMPLEMENTS", "METHOD_CALL", "METHOD_PARAMETER",
                       "FIELD_REFERENCE", "TYPE_USAGE", "EXCEPTION_THROWS"})


def make_instructor_input(binary: Path, aliases: list[dict], output: Path) -> dict:
    """Preserve original owned base class bytes in a deterministic input JAR.

    Target libraries, module/package descriptors and MR override entries never
    enter the instructor scanner. Enclosing and source ownership decisions have
    already been taken from the supplemental metadata pass, independently of
    which nodes happen to have edges. This is graph scope normalization, not a
    rewrite of bytecode. The complete original Maven binary remains preserved.
    """
    target = output / "instructor_input.jar"
    temporary = target.with_suffix(".jar.part")
    rows = []
    with zipfile.ZipFile(binary) as original, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as derived:
        entries = Counter(original.namelist())
        for alias in sorted(aliases, key=lambda r: r["binary_class"]):
            name = alias["binary_class"].replace(".", "/") + ".class"
            if entries[name] != 1:
                raise ValueError(f"Owned binary class does not have one base entry: {name}")
            content = original.read(name)
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            derived.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            rows.append({"binary_class": alias["binary_class"], "class": alias["class"],
                         "jar_entry": name, "bytes": len(content),
                         "class_sha256": hashlib.sha256(content).hexdigest()})
    temporary.replace(target)
    write_csv(output / "instructor_input_classes.csv", rows,
              ["binary_class", "class", "jar_entry", "bytes", "class_sha256"])
    metadata = {
        "file": target.name, "sha256": sha256(target), "source_binary_sha256": sha256(binary),
        "class_entries": len(rows), "class_bytes": sum(r["bytes"] for r in rows),
        "inventory_sha256": sha256(output / "instructor_input_classes.csv"),
        "policy": "Only source-owned base class entries; original class bytes unchanged; sorted ZIP entries with fixed timestamps; no target execution",
    }
    write_json(output / "instructor_input.json", metadata)
    return metadata


def normalize_instructor(output: Path) -> dict:
    """Normalize only instructor rows into the primary unweighted class graph."""
    classes = read_csv(output / "classes.csv")
    nodes = {r["class"] for r in classes}
    annotations = {r["class"] for r in classes if r["kind"] == "annotation"}
    aliases = {r["binary_class"]: r["class"] for r in read_csv(output / "class_aliases.csv")}
    raw = read_csv(output / "instructor_raw.csv")
    required = {"dependeeClass", "dependencyClass", "DependencyType", "DependencySubtype", "Times"}
    if raw and not required <= set(raw[0]):
        raise ValueError("Unexpected instructor CSV schema")
    typed = set()
    excluded, counts = [], Counter()
    raw_types = Counter()
    for row in raw:
        relation = row["DependencyType"]
        if relation not in RELATIONS:
            raise ValueError(f"Unknown instructor relation: {relation}")
        if int(row["Times"]) < 1:
            raise ValueError("Invalid instructor dependency occurrence count")
        raw_types[relation] += 1
        source, target = aliases.get(row["dependeeClass"]), aliases.get(row["dependencyClass"])
        if source is None or target is None:
            reason = ("both_endpoints_outside_owned_scope" if source is None and target is None
                      else "source_outside_owned_scope" if source is None else "target_outside_owned_scope")
        elif source == target:
            reason = "self_after_outer_merge"
        else:
            counts["accepted_raw_typed_rows"] += 1
            typed.add((source, target, relation))
            continue
        counts[reason] += 1
        excluded.append({**row, "reason": reason})
    edges = {(source, target) for source, target, _ in typed}
    write_csv(output / "dependencies_typed.csv",
              [{"source": a, "target": b, "relation": r} for a, b, r in sorted(typed)],
              ["source", "target", "relation"])
    write_csv(output / "dependencies.csv", [{"source": a, "target": b} for a, b in sorted(edges)],
              ["source", "target"])
    write_csv(output / "instructor_excluded_rows.csv", sorted(excluded, key=lambda r: (
        r["dependeeClass"], r["dependencyClass"], r["DependencyType"], r["DependencySubtype"], int(r["Times"]))),
        ["dependeeClass", "dependencyClass", "DependencyType", "DependencySubtype", "Times", "reason"])
    counts.update({"raw_typed_rows": len(raw), "excluded_raw_typed_rows": len(excluded),
                   "unique_typed_edges": len(typed), "unique_directed_edges": len(edges),
                   "duplicate_normalized_typed_rows": counts["accepted_raw_typed_rows"] - len(typed)})
    write_csv(output / "instructor_normalization_counts.csv",
              [{"metric": k, "value": v} for k, v in sorted(counts.items())], ["metric", "value"])
    supplemental_rows = read_csv(output / "supplemental_dependencies_typed.csv")
    supplemental = {(r["source"], r["target"]) for r in supplemental_rows}
    supplemental_types = {}
    for row in supplemental_rows:
        supplemental_types.setdefault((row["source"], row["target"]), set()).add(row["relation"])
    for name, difference in (("supplemental_only_edges.csv", supplemental - edges),
                             ("instructor_only_edges.csv", edges - supplemental)):
        write_csv(output / name, [{"source": a, "target": b, "target_is_annotation": b in annotations,
                                  "supplemental_relations": ";".join(sorted(supplemental_types.get((a, b), set())))}
                                 for a, b in sorted(difference)],
                  ["source", "target", "target_is_annotation", "supplemental_relations"])
    graph = read_graph(output)
    graph.rsf(output / "full.rsf")
    if not set(graph.nodes) == nodes:
        raise ValueError("Instructor normalization changed the independently collected node inventory")
    counts_supplemental = {r["metric"]: int(r["value"]) for r in read_csv(output / "supplemental_extraction_counts.csv")}
    combined = {**counts_supplemental,
                "supplemental_unique_directed_edges": counts_supplemental["unique_directed_edges"],
                "supplemental_unique_typed_edges": counts_supplemental["unique_typed_edges"],
                "unique_directed_edges": len(edges), "unique_typed_edges": len(typed),
                "instructor_raw_typed_rows": len(raw), "instructor_excluded_raw_typed_rows": len(excluded),
                "primary_isolated_classes": len(graph.isolates), "annotation_classes": len(annotations),
                "primary_annotation_target_edges": sum(b in annotations for a, b in edges)}
    write_csv(output / "extraction_counts.csv", [{"metric": k, "value": v} for k, v in sorted(combined.items())],
              ["metric", "value"])
    return {
        "normalization_counts": dict(sorted(counts.items())),
        "raw_relation_counts": dict(sorted(raw_types.items())),
        "relation_counts": dict(sorted(Counter(r for _, _, r in typed).items())),
        "annotation_classes": len(annotations),
        "annotation_isolated_classes": len(annotations.intersection(graph.isolates)),
        "annotation_target_edges": sum(b in annotations for a, b in edges),
        "annotation_source_edges": sum(a in annotations for a, b in edges),
        "supplemental_dependencies": len(supplemental),
        "supplemental_annotation_target_edges": sum(b in annotations for a, b in supplemental),
        "supplemental_only_edges": len(supplemental - edges),
        "supplemental_only_annotation_target_edges": sum(b in annotations for a, b in supplemental - edges),
        "instructor_only_edges": len(edges - supplemental), "shared_edges": len(edges.intersection(supplemental)),
    }


def extract_artifacts(binary: Path, sources: Path, output: Path, *, java: str | None = None,
                      owned_prefixes: tuple[str, ...] = OWNED_PREFIXES,
                      supplemental_classes: Path | None = None) -> dict:
    """Run both original instructor and supplemental passes on one artifact pair."""
    output.mkdir(parents=True, exist_ok=True)
    executable = java_path(java)
    classpath = instructor_classpath()
    supplemental_classes = supplemental_classes or ROOT / "build/extractor"
    command = [executable, "-Xmx1g", "-cp", os.pathsep.join([str(supplemental_classes), str(ROOT / "tools/asm-9.7.1.jar")]),
               "DependencyExtractor", str(binary), str(sources), str(output), ",".join(owned_prefixes)]
    started = time.perf_counter()
    process = subprocess.run(command, capture_output=True, text=True, env=java_env(executable), timeout=180)
    supplemental_seconds = time.perf_counter() - started
    (output / "supplemental.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    write_json(output / "supplemental_command.json", {"argv": command, "exit_code": process.returncode,
                                                    "role": "ownership, enclosing identities, member evidence and sensitivity graph only"})
    if process.returncode:
        raise RuntimeError(f"Supplemental extraction failed: {binary.name}\n{process.stdout}\n{process.stderr}")
    nodes = {r["class"] for r in read_csv(output / "classes.csv")}
    if not all(any(n.startswith(prefix + ".") for prefix in owned_prefixes) for n in nodes):
        raise ValueError("External class survived source-ownership filtering")
    input_metadata = make_instructor_input(binary, read_csv(output / "class_aliases.csv"), output)
    # A failed upstream invocation must not accidentally reuse a previous CSV.
    (output / "instructor_raw.csv").unlink(missing_ok=True)
    instructor_command = [executable, "-Xmx1g", "-cp", os.pathsep.join(map(str, classpath)),
                          "CompCalc.MainClass", str(output / "instructor_input.jar"), str(output / "instructor_raw.csv")]
    instructor_started = time.perf_counter()
    instructor = subprocess.run(instructor_command, capture_output=True, text=True, env=java_env(executable), timeout=180)
    instructor_seconds = time.perf_counter() - instructor_started
    (output / "instructor.log").write_text(instructor.stdout + instructor.stderr, encoding="utf-8")
    write_json(output / "instructor_command.json", {"argv": instructor_command, "exit_code": instructor.returncode,
                                                   "main_class": "CompCalc.MainClass", "instructor_sha256": INSTRUCTOR_SHA256,
                                                   "input_sha256": input_metadata["sha256"],
                                                   "role": "sole relationship source for the primary class graph"})
    if instructor.returncode or not (output / "instructor_raw.csv").exists():
        raise RuntimeError(f"Instructor extraction failed: {binary.name}\n{instructor.stdout}\n{instructor.stderr}")
    comparison = normalize_instructor(output)
    write_json(output / "extractor_comparison.json", comparison)
    stdout_lines = instructor.stdout.strip().splitlines()
    return {"instructor_input": input_metadata, **comparison,
            "supplemental_extraction_seconds": supplemental_seconds,
            "instructor_extraction_seconds": instructor_seconds,
            "extraction_seconds": time.perf_counter() - started,
            "stdout": "\n".join(stdout_lines if len(stdout_lines) <= 5 else stdout_lines[:2] + stdout_lines[-3:]),
            "stdout_log": "instructor.log", "stderr": instructor.stderr.strip()}


def extract_release(row: dict, output_root: Path, *, java: str | None = None) -> dict:
    version = row["version"]
    output = output_root / version
    for kind in ("jar", "sources", "pom"):
        path = ROOT / row[f"{kind}_path"]
        expected = row[f"{kind}_sha256"]
        if sha256(path) != expected:
            raise ValueError(f"Input checksum mismatch: {version} {kind}")
    audit = extract_artifacts(ROOT / row["jar_path"], ROOT / row["sources_path"], output, java=java)
    graph = read_graph(output)
    classes = read_csv(output / "classes.csv")
    counts = {r["metric"]: int(r["value"]) for r in read_csv(output / "extraction_counts.csv")}
    source_names = sorted({r["source_file"] for r in classes})
    source_sizes = []
    with zipfile.ZipFile(ROOT / row["sources_path"]) as archive:
        for name in source_names:
            source_sizes.append({"source_file": name, **count_java_lines(archive.read(name).decode("utf-8", errors="replace"))})
    write_csv(output / "source_sizes.csv", source_sizes)
    metadata = {
        "schema_version": 2,
        "version": version, "tag": row["tag"], "commit_sha": row["commit_sha"], "date": row["release_date"],
        "date_basis": row["date_basis"], "commit_date": row["commit_date"],
        "classes": len(graph.nodes), "dependencies": len(graph.edges), "isolated_classes": len(graph.isolates),
        "owned_source_files": len(source_names), "raw_binary_classes": counts["owned_binary_classes"],
        "merged_binary_classes": counts["owned_binary_classes"] - len(graph.nodes),
        "excluded_binary_classes": counts["excluded_binary_classes"],
        "unique_member_edges": counts["unique_member_edges"],
        **{key: sum(r[key] for r in source_sizes) for key in ("physical_java_lines", "nonblank_java_lines", "java_code_lines")},
        "primary_extractor": "instructor DependencyExtractor (unmodified CompCalc.MainClass)",
        "instructor_jar_sha256": sha256(INSTRUCTOR_JAR),
        "adapter_sha256": sha256(Path(__file__)),
        "toolchain_sha256": sha256(ROOT / "src/evolution/toolchain.py"),
        "extractor_sha256": sha256(ROOT / "java/DependencyExtractor.java"),
        "extractor_sha256_role": "supplemental Java source; primary relationships come solely from instructor_jar_sha256",
        "supplemental_extractor_sha256": sha256(ROOT / "java/DependencyExtractor.java"),
        "binary_sha256": row["jar_sha256"], "sources_sha256": row["sources_sha256"],
        "pom_sha256": row["pom_sha256"],
        "graph_sha256": sha256(output / "dependencies.csv"), "classes_sha256": sha256(output / "classes.csv"),
        "typed_graph_sha256": sha256(output / "dependencies_typed.csv"),
        "instructor_raw_sha256": sha256(output / "instructor_raw.csv"),
        "member_graph_sha256": sha256(output / "member_dependencies.csv"),
        "static_model": "primary instructor symbolic bytecode relationships; supplemental internal declaration-resolved member uses for UE; no target execution or virtual dispatch expansion",
        "source_ownership": "source-file membership AND com.google.common or com.google.thirdparty.publicsuffix namespace; base entries; enclosing metadata merge; explicit shaded implementation exclusions",
        "owned_namespace_prefixes": list(OWNED_PREFIXES),
        "annotation_policy": "retain owned annotation type nodes and ordinary instructor-recorded code references; do not add annotation-application edges from supplemental ASM",
        "instructor_input_policy": "deterministic JAR containing only owned base class entries; bytecode is unchanged",
        **audit,
    }
    write_json(output / "provenance.json", metadata)
    return metadata
```
<!-- END_FULL_SOURCE src/evolution/extraction.py -->

### src/evolution/toolchain.py

SHA-256: `b8d3deb08001980302651b71e51ab668425714a73ed3458865057e5aea1f7af8` · 5,560 bytes

<!-- FULL_SOURCE src/evolution/toolchain.py b8d3deb08001980302651b71e51ab668425714a73ed3458865057e5aea1f7af8 -->
```python
"""Small portable Java toolchain wrapper; target application classes are never executed."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TOOLS = {
    "asm-9.7.1.jar": "8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281",
    "ecj-3.37.0.jar": "cde026ff966b48b5e5f148b6f041ceff3cf4f85cf75155f4ec0f40e4ee14b545",
}
INSTRUCTOR_JAR = ROOT / "third_party/dependency_extractor/DependencyExtractor.jar"
INSTRUCTOR_SHA256 = "8e4e857222dba569cc48ddf2bc58d3ac206d4ee1c0d5228b7b69517016450e9c"
INSTRUCTOR_LIBRARIES = {
    "ant-1.6.5.jar": "f06a601c718a7c9262d74b7ec3baad14c82584e89235089b4f821d6a44d9e1e4",
    "javaparser-1.0.8.jar": "186e3a0c99954c4ddcc103aaae97fc85dce254bb0494e675b1e3901fbc7bce3b",
    "ant.jar": "92f72307e7440f1e352c916f2438d2bbab3ffd2cf730c71316117ad04abadea8",
    "asm-9.7.1.jar": "8cadd43ac5eb6d09de05faecca38b917a040bb9139c7edeb4cc81c740b713281",
}


def java_path(explicit: str | None = None) -> str:
    value = explicit or os.environ.get("EVOLUTION_JAVA")
    local = ROOT / "config/toolchain.local.json"
    if not value and local.exists():
        value = json.loads(local.read_text())["java"]
    value = value or shutil.which("java")
    if not value:
        raise RuntimeError("Install Java 17+ or set EVOLUTION_JAVA to its java executable")
    return str(Path(value).resolve())


def java_env(java: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    home = Path(java_path(java)).parent.parent
    libs = [str(p) for p in (home / "lib", home / "lib/server") if p.is_dir()]
    if libs:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(libs + ([env["LD_LIBRARY_PATH"]] if env.get("LD_LIBRARY_PATH") else []))
    return env


def verify_tools() -> None:
    for name, expected in TOOLS.items():
        path = ROOT / "tools" / name
        if not path.exists():
            raise RuntimeError(f"Missing {path}; run python scripts/fetch_tools.py")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Tool checksum mismatch: {name}")
    if not INSTRUCTOR_JAR.exists():
        raise RuntimeError(f"Missing instructor tool: {INSTRUCTOR_JAR}")
    if hashlib.sha256(INSTRUCTOR_JAR.read_bytes()).hexdigest() != INSTRUCTOR_SHA256:
        raise ValueError("Instructor DependencyExtractor JAR checksum mismatch")


def instructor_classpath() -> list[Path]:
    """Run original CompCalc classes with their unchanged bundled dependencies.

    The original Eclipse jar-in-jar loader fails to locate ASM on this Java 17
    runtime. Extracting its four exact nested JARs and setting -cp is a launcher
    adaptation, not a modification to either the extractor or its libraries.
    No target Guava classes are added to the JVM's executable classpath.
    """
    verify_tools()
    destination = ROOT / "build/instructor-libs"
    destination.mkdir(parents=True, exist_ok=True)
    classpath = [INSTRUCTOR_JAR]
    with zipfile.ZipFile(INSTRUCTOR_JAR) as archive:
        for name, expected in INSTRUCTOR_LIBRARIES.items():
            content = archive.read(name)
            if hashlib.sha256(content).hexdigest() != expected:
                raise ValueError(f"Instructor bundled-library checksum mismatch: {name}")
            target = destination / name
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                temporary = target.with_suffix(target.suffix + ".part")
                temporary.write_bytes(content)
                temporary.replace(target)
            classpath.append(target)
    return classpath


def build_java(java: str | None = None) -> dict:
    verify_tools()
    executable = java_path(java)
    env = java_env(executable)
    version = subprocess.run([executable, "-version"], check=True, capture_output=True, text=True, env=env)
    ecj = str(ROOT / "tools/ecj-3.37.0.jar")
    commands = []
    for name, release, sources, extra in [
        ("extractor", "-17", [ROOT / "java/DependencyExtractor.java"], ["-cp", str(ROOT / "tools/asm-9.7.1.jar")]),
        ("acdc", "-8", sorted((ROOT / "third_party/acdc/acdc").glob("*.java")), []),
    ]:
        out = ROOT / "build" / name
        out.mkdir(parents=True, exist_ok=True)
        if not sources:
            raise RuntimeError(f"No {name} sources found")
        command = [executable, "-jar", ecj, release, "-nowarn", *extra, "-d", str(out), *map(str, sources)]
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        commands.append({"component": name, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            raise RuntimeError(f"Java compilation failed for {name}: {result.stdout}\n{result.stderr}")
    instructor_cp = instructor_classpath()
    details = {"java_version": (version.stderr + version.stdout).strip(), "compiler": "Eclipse ECJ 3.37.0", "asm": "9.7.1", "builds": commands,
               "primary_extractor": "unmodified instructor CompCalc.MainClass",
               "instructor_sha256": INSTRUCTOR_SHA256,
               "instructor_classpath": [str(p.relative_to(ROOT)) for p in instructor_cp],
               "supplemental_extractor": "java/DependencyExtractor.java (ownership, member evidence and sensitivity graph)"}
    (ROOT / "build/toolchain.json").write_text(json.dumps(details, indent=2) + "\n")
    return details
```
<!-- END_FULL_SOURCE src/evolution/toolchain.py -->

### tests/test_extractor.py

SHA-256: `17fc3d0f28627b0c04db15e3df44a1c6f1710afce25826409fe05e5c8d5cdb9f` · 18,273 bytes

<!-- FULL_SOURCE tests/test_extractor.py 17fc3d0f28627b0c04db15e3df44a1c6f1710afce25826409fe05e5c8d5cdb9f -->
```python
"""Compile a tiny owned fixture and verify the real extractor's CSV evidence.

The fixture covers the course's seven relations and the normalization and
declaration-resolution cases that can silently corrupt UE.  Target fixture
classes are never executed.  A small ASM pass changes symbolic owners to legal
inherited owners, making the lookup tests independent of ECJ's constant-pool
owner choices.  The field case exercises the JVMS interface-before-superclass
rule even though Java source rejects the corresponding ambiguous field syntax.
"""

import csv
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

from evolution.omnipresent import detect_omnipresent
from evolution.extraction import extract_artifacts
from evolution.toolchain import ROOT, java_env, java_path, verify_tools


SAMPLE_SOURCE = r"""
package fixture;

public class Sample extends Base implements Contract {
    public Used hold;
    @Mark public Result process(Argument argument) throws Problem {
        Used used = new Used();
        used.call();
        int ignored = used.value;
        if (ignored < 0) throw new Problem();
        return new Result();
    }
    public Used inheritedCalls(Child child) {
        child.inherited(null);
        return child.inheritedField;
    }
    public Used defaultCall(DefaultChild child) { return child.chosen(); }
    public Used dollar(Dollar$Top value) { return value.fetch(); }
    public Object external() { return external.Library.convert(); }
    public Runnable anonymous() {
        return new Runnable() { public void run() { Used.utility(); } };
    }
    class Inner { public void run() { Used.utility(); } }
    static class Nested { public void run() { Used.utility(); } }
}
class Base {}
interface ParentContract {}
interface Contract extends ParentContract {}
class Used { public int value; public void call() {} public static void utility() {} }
class Argument {}
class Result {}
class Problem extends Exception {}
@interface Mark {}
class Grand {
    public Used inheritedField;
    public Used inherited(Argument argument) { return null; }
}
class Middle extends Grand {}
interface Shadow { default Used inherited(Argument argument) { return null; } }
class Child extends Middle implements Shadow {}
interface RootDefault { default Used chosen() { return null; } }
interface MoreDefault extends RootDefault { default Used chosen() { return null; } }
class DefaultChild implements RootDefault, MoreDefault {}
interface FieldInterface { Used shared = new Used(); }
class FieldParent { public static Used shared = new Used(); }
class FieldChild extends FieldParent implements FieldInterface {}
class FieldUser { Used lookup() { return FieldInterface.shared; } }
class GenericOuter<T> { class Inner<U> {} }
class TypeArg {}
// A legal top-level dollar name catches the old phantom Arg$Inner signature bug.
class TypeArg$Inner {}
class OtherArg {}
class GenericUser { GenericOuter<TypeArg>.Inner<OtherArg> value; }
class Dollar$Top { public Used fetch() { return null; } }
class ExplodingInitializer {
    static { if (System.nanoTime() != 0) throw new AssertionError("Do not execute target classes"); }
}
"""


SYMBOLIC_OWNER_REWRITER = r"""
import java.nio.file.*;
import org.objectweb.asm.*;
public class SymbolicOwnerRewriter {
    public static void main(String[] args) throws Exception {
        for (String className : new String[]{"fixture/Sample", "fixture/FieldUser"}) {
            Path path = Paths.get(args[0], className + ".class");
            ClassReader reader = new ClassReader(Files.readAllBytes(path));
            ClassWriter writer = new ClassWriter(0);
            reader.accept(new ClassVisitor(Opcodes.ASM9, writer) {
                public MethodVisitor visitMethod(int a, String n, String d, String s, String[] e) {
                    return new MethodVisitor(Opcodes.ASM9, super.visitMethod(a,n,d,s,e)) {
                        public void visitMethodInsn(int op, String owner, String name, String desc, boolean itf) {
                            if (name.equals("inherited")) owner = "fixture/Child";
                            if (name.equals("chosen")) owner = "fixture/DefaultChild";
                            super.visitMethodInsn(op,owner,name,desc,itf);
                        }
                        public void visitFieldInsn(int op, String owner, String name, String desc) {
                            if (name.equals("inheritedField")) owner = "fixture/Child";
                            if (name.equals("shared")) owner = "fixture/FieldChild";
                            super.visitFieldInsn(op,owner,name,desc);
                        }
                    };
                }
            }, 0);
            Files.write(path, writer.toByteArray());
        }
    }
}
"""


class TestBytecodeExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_tools()
        cls.java = java_path()
        cls.env = java_env(cls.java)
        (ROOT / "build").mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(prefix="extractor-fixture-", dir=ROOT / "build")
        cls.work = Path(cls.temporary.name)
        source = cls.work / "src"
        (source / "fixture").mkdir(parents=True)
        (source / "external").mkdir()
        (source / "com/google/common").mkdir(parents=True)
        (source / "com/google/thirdparty/publicsuffix").mkdir(parents=True)
        (source / "fixture/Sample.java").write_text(SAMPLE_SOURCE)
        (source / "fixture/MissingSource.java").write_text("package fixture; public class MissingSource {}\n")
        (source / "external/Library.java").write_text(
            "package external; public class Library { public static Object convert() { return null; } }\n"
        )
        extra_sources = {
            "com/google/common/PublicApi.java": """package com.google.common;
                @CompatibilityMarker public class PublicApi {
                    public com.google.thirdparty.publicsuffix.PublicSuffixType suffix() {
                        return com.google.thirdparty.publicsuffix.PublicSuffixType.parse();
                    }
                    public Class<SemanticMarker> semanticMarker() { return SemanticMarker.class; }
                }""",
            "com/google/common/CompatibilityMarker.java": "package com.google.common; public @interface CompatibilityMarker {}",
            "com/google/common/SemanticMarker.java": "package com.google.common; public @interface SemanticMarker {}",
            "com/google/common/Isolated.java": "package com.google.common; public class Isolated {}",
            "com/google/thirdparty/publicsuffix/PublicSuffixType.java": """package com.google.thirdparty.publicsuffix;
                public class PublicSuffixType {
                    public static PublicSuffixType parse() { return new PublicSuffixType(); }
                    public static class Nested {}
                }""",
        }
        for name, content in extra_sources.items():
            (source / name).write_text(content)
        helper = cls.work / "SymbolicOwnerRewriter.java"
        helper.write_text(SYMBOLIC_OWNER_REWRITER)
        cls.binary = cls.work / "binary"
        cls.extractor = cls.work / "extractor"
        cls.binary.mkdir()
        cls.extractor.mkdir()
        ecj = ROOT / "tools/ecj-3.37.0.jar"
        cls.asm = ROOT / "tools/asm-9.7.1.jar"
        cls.run_command([
            cls.java, "-jar", str(ecj), "-17", "-nowarn", "-g", "-d", str(cls.binary),
            *[str(path) for path in sorted(source.rglob("*.java"))],
        ])
        cls.run_command([
            cls.java, "-jar", str(ecj), "-17", "-nowarn", "-cp", str(cls.asm),
            "-d", str(cls.extractor), str(ROOT / "java/DependencyExtractor.java"), str(helper),
        ])
        cls.run_command([
            cls.java, "-cp", os.pathsep.join((str(cls.extractor), str(cls.asm))),
            "SymbolicOwnerRewriter", str(cls.binary),
        ])
        cls.jar = cls.work / "fixture.jar"
        with ZipFile(cls.jar, "w") as archive:
            for path in sorted(cls.binary.rglob("*.class")):
                archive.write(path, path.relative_to(cls.binary).as_posix())
            archive.writestr("META-INF/versions/17/fixture/Sample.class", (cls.binary / "fixture/Sample.class").read_bytes())
        cls.sources_jar = cls.work / "fixture-sources.jar"
        with ZipFile(cls.sources_jar, "w") as archive:
            archive.write(source / "fixture/Sample.java", "fixture/Sample.java")
            archive.write(source / "external/Library.java", "external/Library.java")
            for name in sorted(extra_sources):
                archive.write(source / name, name)
        cls.output = cls.work / "out"
        cls.run_extractor(cls.output)
        cls.classes = cls.read_csv("classes.csv")
        cls.aliases = cls.read_csv("class_aliases.csv")
        cls.relations = cls.read_csv("supplemental_dependencies_typed.csv")
        cls.members = cls.read_csv("member_dependencies.csv")
        cls.counts = {r["metric"]: int(r["value"]) for r in cls.read_csv("supplemental_extraction_counts.csv")}
        cls.class_names = {r["class"] for r in cls.classes}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @classmethod
    def run_command(cls, command):
        result = subprocess.run(command, env=cls.env, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(f"Fixture command failed:\n{result.stdout}\n{result.stderr}")
        return result

    @classmethod
    def run_extractor(cls, output):
        return extract_artifacts(cls.jar, cls.sources_jar, output, java=cls.java,
                                 owned_prefixes=("fixture", "com.google.common", "com.google.thirdparty.publicsuffix"),
                                 supplemental_classes=cls.extractor)

    @classmethod
    def read_csv(cls, name):
        with (cls.output / name).open(newline="") as stream:
            return list(csv.DictReader(stream))

    def test_all_seven_lecture_relations_have_real_evidence(self):
        actual = {(r["source"], r["target"], r["relation"]) for r in self.relations}
        expected = {
            ("fixture.Sample", "fixture.Base", "EXTENDS"),
            ("fixture.Sample", "fixture.Contract", "IMPLEMENTS"),
            ("fixture.Sample", "fixture.Argument", "METHOD_PARAMETER"),
            ("fixture.Sample", "fixture.Result", "TYPE_USAGE"),
            ("fixture.Sample", "fixture.Problem", "EXCEPTION_THROWS"),
            ("fixture.Sample", "fixture.Used", "FIELD_REFERENCE"),
            ("fixture.Sample", "fixture.Used", "METHOD_CALL"),
        }
        self.assertTrue(expected <= actual, expected - actual)
        self.assertEqual({r["relation"] for r in self.relations}, {r[2] for r in expected})

    def test_inner_and_anonymous_merge_but_original_members_stay_distinct(self):
        aliases = {r["binary_class"]: r["class"] for r in self.aliases}
        for binary in ("fixture.Sample$1", "fixture.Sample$Inner", "fixture.Sample$Nested"):
            self.assertEqual(aliases[binary], "fixture.Sample")
        callers = {
            r["source_member"] for r in self.members
            if r["source_class"] == "fixture.Sample" and r["target_member"] == "fixture.Used#M:utility()V"
        }
        self.assertEqual(callers, {
            "fixture.Sample$1#M:run()V",
            "fixture.Sample$Inner#M:run()V",
            "fixture.Sample$Nested#M:run()V",
        })
        for edge in self.members:
            self.assertNotEqual(edge["source_class"], edge["target_class"])

    def test_legitimate_top_level_dollar_names_are_not_merged(self):
        self.assertIn("fixture.Dollar$Top", self.class_names)
        self.assertIn("fixture.TypeArg$Inner", self.class_names)
        aliases = {r["binary_class"]: r["class"] for r in self.aliases}
        self.assertEqual(aliases["fixture.Dollar$Top"], "fixture.Dollar$Top")
        self.assertTrue(any(r["target_member"] == "fixture.Dollar$Top#M:fetch()Lfixture/Used;" for r in self.members))

    def test_inherited_members_use_declaring_owner_and_jvm_lookup_order(self):
        calls = {(r["source_class"], r["target_member"]) for r in self.members}
        self.assertIn(("fixture.Sample", "fixture.Grand#M:inherited(Lfixture/Argument;)Lfixture/Used;"), calls)
        self.assertIn(("fixture.Sample", "fixture.Grand#F:inheritedFieldLfixture/Used;"), calls)
        self.assertNotIn(("fixture.Sample", "fixture.Shadow#M:inherited(Lfixture/Argument;)Lfixture/Used;"), calls)
        self.assertIn(("fixture.Sample", "fixture.MoreDefault#M:chosen()Lfixture/Used;"), calls)
        self.assertNotIn(("fixture.Sample", "fixture.RootDefault#M:chosen()Lfixture/Used;"), calls)
        self.assertIn(("fixture.FieldUser", "fixture.FieldInterface#F:sharedLfixture/Used;"), calls)
        self.assertNotIn(("fixture.FieldUser", "fixture.FieldParent#F:sharedLfixture/Used;"), calls)

    def test_generic_arguments_do_not_replace_the_enclosing_owner(self):
        targets = {r["target"] for r in self.relations if r["source"] == "fixture.GenericUser"}
        self.assertTrue({"fixture.GenericOuter", "fixture.TypeArg", "fixture.OtherArg"} <= targets)
        self.assertNotIn("fixture.TypeArg$Inner", targets)

    def test_all_outputs_exclude_external_and_unowned_class_endpoints(self):
        self.assertNotIn("external.Library", self.class_names)
        self.assertNotIn("fixture.MissingSource", self.class_names)
        excluded = {r["binary_class"]: r["reason"] for r in self.read_csv("excluded_classes.csv")}
        self.assertEqual(excluded["external.Library"], "outside_project_namespace")
        self.assertEqual(excluded["fixture.MissingSource"], "no_owned_source_file")
        for edge in self.relations:
            self.assertIn(edge["source"], self.class_names)
            self.assertIn(edge["target"], self.class_names)
            self.assertNotEqual(edge["source"], edge["target"])
        for edge in self.members:
            self.assertIn(edge["source_class"], self.class_names)
            self.assertIn(edge["target_class"], self.class_names)
        self.assertEqual(self.counts["multi_release_class_entries_excluded"], 1)
        self.assertGreater(self.counts["member_resolution_cache_hits"], 0)

    def test_real_extracted_rows_feed_ue_without_identity_conflicts(self):
        result = detect_omnipresent(self.class_names, self.members)
        self.assertEqual(result.stats.excluded_external_edges, 0)
        self.assertEqual(result.stats.excluded_intraclass_edges, 0)
        self.assertEqual(result.stats.duplicate_member_edges, 0)
        self.assertEqual(result.stats.unique_member_edges, len(self.members))
        self.assertIn("fixture.Used", result.by_class())

    def test_repeated_extraction_is_byte_for_byte_reproducible(self):
        second = self.work / "out-repeat"
        self.run_extractor(second)
        for first in self.output.glob("*.csv"):
            self.assertEqual(first.read_bytes(), (second / first.name).read_bytes(), first.name)

    def test_primary_edges_are_exactly_normalized_unmodified_instructor_rows(self):
        aliases = {r["binary_class"]: r["class"] for r in self.aliases}
        expected = set()
        for row in self.read_csv("instructor_raw.csv"):
            source, target = aliases.get(row["dependeeClass"]), aliases.get(row["dependencyClass"])
            if source and target and source != target:
                expected.add((source, target, row["DependencyType"]))
        actual = {(r["source"], r["target"], r["relation"]) for r in self.read_csv("dependencies_typed.csv")}
        self.assertEqual(actual, expected)
        pairs = {(r["source"], r["target"]) for r in self.read_csv("dependencies.csv")}
        self.assertEqual(pairs, {(a, b) for a, b, _ in expected})
        self.assertTrue(all(a in self.class_names and b in self.class_names and a != b for a, b in pairs))

    def test_publicsuffix_is_owned_inner_merged_and_instructor_input_is_scoped(self):
        publicsuffix = "com.google.thirdparty.publicsuffix.PublicSuffixType"
        self.assertIn(publicsuffix, self.class_names)
        aliases = {r["binary_class"]: r["class"] for r in self.aliases}
        self.assertEqual(aliases[publicsuffix + "$Nested"], publicsuffix)
        pairs = {(r["source"], r["target"]) for r in self.read_csv("dependencies.csv")}
        self.assertIn(("com.google.common.PublicApi", publicsuffix), pairs)
        with ZipFile(self.output / "instructor_input.jar") as derived, ZipFile(self.jar) as original:
            self.assertEqual(set(derived.namelist()), {n.replace(".", "/") + ".class" for n in aliases})
            self.assertTrue(all(not n.startswith(("META-INF/", "external/")) for n in derived.namelist()))
            self.assertNotIn("fixture/MissingSource.class", derived.namelist())
            for name in derived.namelist():
                self.assertEqual(derived.read(name), original.read(name))

    def test_annotation_applications_are_only_supplemental_but_nodes_and_code_references_remain(self):
        primary = {(r["source"], r["target"]) for r in self.read_csv("dependencies.csv")}
        supplementary = {(r["source"], r["target"]) for r in self.read_csv("supplemental_dependencies.csv")}
        compatibility = ("com.google.common.PublicApi", "com.google.common.CompatibilityMarker")
        semantic = ("com.google.common.PublicApi", "com.google.common.SemanticMarker")
        self.assertIn(compatibility, supplementary)
        self.assertNotIn(compatibility, primary)
        self.assertIn(semantic, primary)
        self.assertIn("com.google.common.CompatibilityMarker", self.class_names)
        self.assertIn("com.google.common.Isolated", self.class_names)
        incident = {name for edge in primary for name in edge}
        self.assertNotIn("com.google.common.CompatibilityMarker", incident)
        self.assertNotIn("com.google.common.Isolated", incident)
        comparison = json.loads((self.output / "extractor_comparison.json").read_text())
        self.assertGreater(comparison["supplemental_only_annotation_target_edges"], 0)


if __name__ == "__main__":
    unittest.main()
```
<!-- END_FULL_SOURCE tests/test_extractor.py -->

### third_party/acdc/acdc/ACDC.java

SHA-256: `e9ace5e1db106745fcb30bb2475ab75d23910f9fbafd8487931b86dbed69bb27` · 10,378 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/ACDC.java e9ace5e1db106745fcb30bb2475ab75d23910f9fbafd8487931b86dbed69bb27 -->
```java
package acdc;
import java.util.*;

import javax.swing.JFrame;
import javax.swing.JScrollPane;
import javax.swing.JTree;
import javax.swing.tree.DefaultMutableTreeNode;

/**
 * This application facilitates the task of recovering the structure
 * of large and complex software systems in an automatic way by clustering.
 * 
 * The data structure used to represent the components of the software system
 * is a tree, which is clustered incrementally by using several patterns. 
 * 
 * Assumptions made:
 * ACDC will cluster the children of the root in the input.
 * Once an object has been clustered, it is never removed from its cluster
 * (but it might get further clustered within its cluster)
 */
public class ACDC
{

/**
 * Exits the program with an error message which reminds the user how to
 * run this application. 
 * The string s represents the concatenation of characters representing
 * allowable clustering patterns to be used in this program, e.g. 'b' - 
 * body-header pattern, 's'- subgraph pattern , 'o' - orphan adoption etc.
 * @param run_name 
 */
  static void err_AND_exit(String run_name)
  {
	IO.put("USAGE: " + run_name  + " <.ta or .rsf input file> <.rsf output file> [-/+patterns] [options]",0);
		
		IO.put("\nSupported patterns include:",0);
  		IO.put("  B              Body Header",0);
  		IO.put("  S              SubGraph Dominator",0);
  		IO.put("  O              Orphan Adoption",0);
		IO.put("Pattern formats:",0);
		IO.put("<no pattern>     Assumes an input of +BSO and executes the patterns in that order",0);
		IO.put("+pattern(s)      Executes ONLY specified patterns in the given order",0);
		IO.put("-pattern(s)	     Assumes an execution of patterns given by +BSO but removes specified",0); 
		IO.put("                 patterns and executes remaining ones",0);
		
		IO.put("\nPossible options include:",0);
		IO.put("  -d1            Prints progress report messages to standard output",0);
		IO.put("  -d2            Prints detailed debugging info to standard output",0);
 		IO.put("  -h             Prints this synopsis of standard options and exits (other arguments are ignored)",0);
		IO.put("  -l[integer]    Requests that clusters formed in SubGraph have a maximum size\n",0); 		      
  		IO.put("By default, ACDC generates a flat decomposition containing fine-grained clusters.",0);
  		IO.put("The following options can modify this:",0);
		IO.put("  -a[systemName] Generates a hierarchical decomposition (contains nested clusters)",0);
		IO.put("  -u	     Generates a flat decomposition containing only the top level clusters\n",0);
		IO.put("  -t	     Displays the generated decomposition graphically (output file is also created)",0);
		
		System.exit(1);
  }

/**
 * Returns true if the string s1 is made up only of characters found
 * in the string s2; else returns false.
 */
  private static boolean matches(String s1, String s2)
 {
	boolean containsNoOther = true; 
	Vector v = new Vector(s2.length()); 

	for(int i=0 ; i<s2.length() ; i++)
	    v.add(Character.toString(s2.charAt(i)));
	  
	for(int j=0; j<s1.length(); j++)
	{
		if (v.contains(Character.toString(s1.charAt(j))))
			;
		else 
			containsNoOther = false;    
	}
	return containsNoOther;
  }
  
	private static String subtract (String s1, String s2)
	{
		StringBuffer result = new StringBuffer(s1);
		for (int i=0; i< s2.length(); i++)
		{
			int pos = result.indexOf(s2.substring(i,i+1));
			result = result.replace(pos,pos+1,"");
		}
		return result.toString();
	}
  
  public static void main (String [] args)
  {
    String run_name = "java acdc.ACDC";
    for (int i= 0; i<args.length; i++)
    {
        if (args[i].equals("-6431")) run_name = "acdc";
    }
    
    //if one of the given args is "-h", print Help message, then exit
    for(int u=0; u<args.length; u++)
    {
    	if(args[u].equalsIgnoreCase("-h"))
    	{
			err_AND_exit(run_name);	
    	}
    }
    
	IO.set_debug_level(0);
    
    String inputName, outputName;
    
    int maxClusterSize = 20; //used by SubGraph pattern
    boolean gui = false;
       
    // parse input arguments
    if (args.length<2)
    {   
    	 IO.put("\nToo few arguments.",0);
    	 err_AND_exit(run_name);
    }
    
	inputName = args[0]; 
    outputName = args[1];
 
	InputHandler input = null;
	if(inputName.endsWith(".ta") || inputName.endsWith(".rsf"))
		input = new TAInput();
   
	else if(inputName.endsWith(".gxl"))
	{
		IO.put("GXL input is not supported yet.",0);
		IO.put("Hopefully in the next version...",0);
		System.exit(0);
	}
    
	else
	{
		IO.put("Unrecognized input format",0);
		IO.put("Accepted formats are RSF and TA (extensions .rsf and .ta)",0);
		System.exit(0);
	}
	
	OutputHandler output = null;
    
	if (outputName.endsWith(".rsf"))
	{
		output = new RSFOutput();
	}
	else if (outputName.endsWith(".ta"))
	{
		IO.put("TA is not a supported output format yet.",0);
		IO.put("Hopefully in the next version...",0);
		System.exit(0);
	}
	else if(outputName.endsWith(".gxl"))
	{
		IO.put("GXL is not a supported output format yet.",0);
		IO.put("Hopefully in the next version...",0);
		System.exit(0);
	}
	else
	{
		IO.put("Unrecognized output format",0);
		IO.put("Only RSF is supported at this point (extensions .rsf)",0);
		System.exit(0);
	}
		 
	// If it got to this line, we are dealing with at least two args
	// Code executes for 2 or more arguments 

	final String defaultPatterns = "bso";
	String selectedPatterns = null;
    boolean patternsSpecified = false;
    Pattern inducer = null;
	
	// Create a tree with a dummy root
	Node dummy = new Node ("ROOT", "Dummy");
	DefaultMutableTreeNode root = new DefaultMutableTreeNode (dummy);
	dummy.setTreeNode(root);
	
	for (int i= 2; i<args.length; i++)
	{
		final boolean startsWithPlus = args[i].charAt(0) == '+';
		final boolean startsWithMinus = args[i].charAt(0) == '-';
		final String rest = args[i].substring(1);
		final boolean onlyPatterns = matches(rest, defaultPatterns);
		if (startsWithPlus && onlyPatterns)
		{
			if (patternsSpecified)
			{
				IO.put("Duplicate pattern option.",0);
				System.exit(0);
			}
			else
			{
				selectedPatterns = rest; 
				patternsSpecified = true;
			}
		}
		else if (startsWithMinus && onlyPatterns)
		{
			if (patternsSpecified)
			{
				IO.put("Duplicate pattern option.",0);
				System.exit(0);
			}
			else
			{
				selectedPatterns = subtract(defaultPatterns, rest); 
				patternsSpecified = true;
			}
		}
		else if (startsWithMinus && rest.equalsIgnoreCase("d1"))
		{
			IO.set_debug_level(1);
		}
		else if (startsWithMinus && rest.equalsIgnoreCase("d2"))
		{
			IO.set_debug_level(2);
		}
        else if (startsWithMinus && rest.equalsIgnoreCase("6431"))
        {
            run_name = "acdc";
        }
		else if (startsWithMinus && (rest.charAt(0) == 'l'))
		{
			try
			{ 
				maxClusterSize = Integer.parseInt(rest.substring(1));	
			}
			catch (NumberFormatException n) 
			{
				IO.put("Option -l must be followed by a positive integer.",0);
				System.exit(0);
			}
			if (maxClusterSize < 1)
			{
				IO.put("Option -l must be followed by a positive integer.",0);
				System.exit(0);
			}
		}
		else if (startsWithMinus && rest.equalsIgnoreCase("a"))
		{
			inducer = new FullOutput(root,"ROOT");
		}
		else if (startsWithMinus && (rest.length() > 1) && (rest.substring(0,1).equalsIgnoreCase("a")))
		{
			inducer = new FullOutput(root,rest.substring(1));
		}
		else if (startsWithMinus && rest.equalsIgnoreCase("u"))
		{
			inducer = new UpInducer(root);
		}
		else if (startsWithMinus && rest.equalsIgnoreCase("t"))
		{
			gui = true;
		}
		else
		{
			IO.put("Unrecognized option: " + args[i],0);
			System.exit(0);
		}
	}
	
	if (selectedPatterns == null)
		selectedPatterns = defaultPatterns;
	if (inducer == null)
		inducer = new DownInducer(root);
			   	
    IO.put ("Input File: " + inputName,1);
    IO.put ("Output File: " + outputName,1);
    IO.put("Patterns: " + selectedPatterns,1);
    IO.put("Cluster Size: " + maxClusterSize,1);

	// Populate the tree from the input file   
    input.readInput(inputName, root);
    
//    Pattern b = new BodyHeader(root);
//    Pattern s = new SubGraph(root, maxClusterSize);
//    Pattern o = new OrphanAdoption(root);
//    Pattern r = new ReverseOrphanAdoption(root);
    //Pattern e = new EdgeInduction(root);
    //add new pattern here

	Vector vpatterns = new Vector(); //will contain the ordered patterns to be executed
    
	for(int j=0; j<selectedPatterns.length(); j++)
	{    
		switch (selectedPatterns.charAt(j))
	    {
		case 'b':
		vpatterns.add(new BodyHeader(root));
		//vpatterns.add(b);
			    break;
		case 's':
		vpatterns.add(new SubGraph(root,maxClusterSize)); 
		//vpatterns.add(s); 
			    break;
		case 'o':
		vpatterns.add(new OrphanAdoption(root)); 
		//vpatterns.add(o); 
			    break;
		// Add new pattern here
		default:   
				IO.put("Serious error.",0);
				System.exit (0);
		}
	}

	// Induce all edges
	Vector allNodes = Pattern.allNodes(root);
	Pattern.induceEdges(allNodes, root);

	// Execute the patterns
    Iterator iv = vpatterns.iterator();
    while (iv.hasNext())
    {
		Pattern p = (Pattern) iv.next();
		IO.put("Executing " + p.getName() + " pattern...",1);
		p.execute();
    }

	// Take care of any objects that were not clustered
	Pattern c = new ClusterLast(root);
	c.execute();
	
    // Create output file
	IO.put("Creating output...",1);
	inducer.execute();
	output.writeOutput(outputName, root);
	IO.put("Finished!",1);
    
    // Create GUI 
    if (gui)
    {
		displayTree(root);
    }
  }

	private static void displayTree(DefaultMutableTreeNode root) 
	{
		JTree nodeTree = new JTree (root);
		nodeTree.setShowsRootHandles (true);
		nodeTree.putClientProperty ("JTree.lineStyle", "Horizontal");
		nodeTree.putClientProperty ("JTree.lineStyle", "Angled");
		JFrame frame = new JFrame ("File Node Partition");
		frame.setDefaultCloseOperation (JFrame.EXIT_ON_CLOSE);
		frame.getContentPane ().add (new JScrollPane (nodeTree), "Center");
		frame.setSize (400, 600);
		frame.setVisible (true);
	}
	
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/ACDC.java -->

### third_party/acdc/acdc/BodyHeader.java

SHA-256: `bde4bfa03871c3d3202337d2f87263440aec45e35d8b3e1ff8e65d056f87eee3` · 7,194 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/BodyHeader.java bde4bfa03871c3d3202337d2f87263440aec45e35d8b3e1ff8e65d056f87eee3 -->
```java
package acdc;
import java.util.Enumeration;
import java.util.Vector;
import javax.swing.tree.DefaultMutableTreeNode;

/**
 * This pattern lumps a header file (a .h file) and a body file (a .c file)
 * into a cluster. The cluster is named using the common part of the component
 * files names followed by the suffix ".ch". 
 * If clustering has already been done, a message is output to  the user
 * Commented out lines that modify vTree on the fly
 */
 public class BodyHeader extends Pattern
 {
	public BodyHeader(DefaultMutableTreeNode _root)
	{
		super(_root);
		name = "Body Header";
	}

	public void execute ()
	{
		Vector vModified = new Vector();//will contain nodes which were moved
		Vector vTree = allNodes(root);
		
		//traverse the files with extension .c or .h in the tree looking for
		//their counterpart file with extension .h and respectively .c 		
    	for (int i=0; i<vTree.size(); i++)
		{
			Node ncurr = (Node)vTree.elementAt(i);
			DefaultMutableTreeNode curr = (DefaultMutableTreeNode)ncurr.getTreeNode();
                              			
      		if (ncurr.isFile())
			{
				IO.put("Considering file: " + ncurr.getName(),2);
				//if the current .h or .c file is not in the vector vTree, it means that its
				//counterpart file was checked and a cluster containing has been created 
				if (((ncurr.getName().endsWith(".c")) || (ncurr.getName().endsWith(".h")))) // Removed this: && vTree.contains(ncurr))
      			{
					DefaultMutableTreeNode curr_parent = (DefaultMutableTreeNode)curr.getParent();

					if (alreadyClustered(curr_parent))
					{
						IO.put("\tAlready in a body-header cluster",2);
					} 
					else
					{	
						String toFind = "";
						// Loop through the vector of remaining .h and .c 
						// files to find counterpart file
						for(int j = 0; j < vTree.size(); j++)
						{	
							Node vnode = (Node)vTree.get(j);
							IO.put("\tConsidering other file: " + vnode.getName(),2);
							DefaultMutableTreeNode vtnode = (DefaultMutableTreeNode)vnode.getTreeNode();							
							if((ncurr.getName().endsWith(".c")))
							{
							    toFind = ncurr.getName().substring(0, ncurr.getName().length()-2) + ".h";;
							}
							else if((ncurr.getName().endsWith(".h")))
							    toFind = ncurr.getName().substring(0, ncurr.getName().length()-2) + ".c";
							
							if(vnode.getName().equalsIgnoreCase(toFind))
							{	   
								String filename = ncurr.getName().substring(0, ncurr.getName().length()-2);
								//create the new cluster node which will have extension .ch
								Node cluster_node = new Node(filename + ".ch", "cModule");
								DefaultMutableTreeNode tcluster = new DefaultMutableTreeNode(cluster_node);
								cluster_node.setTreeNode(tcluster);
								
								//add the new cluster node under the parent of the current node in the traversal
								curr_parent.add(tcluster);
								
								//make the files with extension .c and .h children of the new cluster node
								tcluster.add(curr);
								tcluster.add(vtnode);
								
								IO.put("\tA cluster called " +
									cluster_node.getName() + " was created containing " +
                                    ncurr.getName() + ", " + vnode.getName(),2);
								
								
		    					        Enumeration evt = vtnode.breadthFirstEnumeration();
							        while(evt.hasMoreElements())
							        {
		    						    DefaultMutableTreeNode ec = (DefaultMutableTreeNode)evt.nextElement();
								    if(!vModified.contains((Node)ec.getUserObject()))
									vModified.add((Node)ec.getUserObject());
							        }
		    
							        Enumeration ecurr= curr.breadthFirstEnumeration();
							        while(ecurr.hasMoreElements())
							        {
		    						    DefaultMutableTreeNode em = (DefaultMutableTreeNode)ecurr.nextElement();
								    if(!vModified.contains((Node)em.getUserObject()))
								    	vModified.add((Node)em.getUserObject());
							        }
		   						
								//remove the files with extension .c and .h from the vector
								//vTree.removeElement(vnode);
								//vTree.removeElement(ncurr);
								//vTree.trimToSize();
								break;				
							}
							else //no counterpart file was found in the vector
							{
							     //vTree.removeElement(ncurr);
							     //vTree.trimToSize();
							}
						}// end for

					}//end else
      			}
			}// end if isFile
		}// end for i
	   
	    induceEdges(vModified,root);

	} // end execute

	private boolean alreadyClustered(DefaultMutableTreeNode curr_parent)
	{	
		Node ncurr_parent = (Node) curr_parent.getUserObject();
		boolean isCModule = ncurr_parent.getName().endsWith(".ch");
		boolean hasTwoKids = (curr_parent.getChildCount() == 2);
		DefaultMutableTreeNode first_child = (DefaultMutableTreeNode) curr_parent.getFirstChild();
		Node nfirst_child = (Node)first_child.getUserObject();
		DefaultMutableTreeNode second_child = (DefaultMutableTreeNode) curr_parent.getLastChild();
		Node nsecond_child = (Node)second_child.getUserObject();
		boolean sameBaseNames = ncurr_parent.getBaseName().equalsIgnoreCase(nfirst_child.getBaseName()) &&
								ncurr_parent.getBaseName().equalsIgnoreCase(nsecond_child.getBaseName());
		boolean dotCHFiles = (nfirst_child.getName().endsWith(".c") && nsecond_child.getName().endsWith(".h")) ||
							 (nfirst_child.getName().endsWith(".h") && nsecond_child.getName().endsWith(".c"));
							 
		return isCModule && hasTwoKids && sameBaseNames && dotCHFiles;
//		// Parent has exactly two children
//		if(curr_parent.getChildCount() == 2)
//		{
//			DefaultMutableTreeNode first_child = (DefaultMutableTreeNode) curr_parent.getFirstChild();
//			Node nfirst_child = (Node)first_child.getUserObject();
//							
//			DefaultMutableTreeNode second_child = (DefaultMutableTreeNode) curr_parent.getLastChild();
//			Node nsecond_child = (Node)second_child.getUserObject();
//
//			//checks nodes for having identical names with ".c" and ".h" as their extension
//			//clustering has been done before so don't do anything
//			//just remove their names from the vector which contains the files with ".c" and ".h" ext.
//			// The removing part has been commented out
//			if (((nfirst_child.getName().endsWith(".c") && nsecond_child.getName().endsWith(".h"))
//				|| (nfirst_child.getName().endsWith(".h") && nsecond_child.getName().endsWith(".c")))
//				&& (nfirst_child.getBaseName().equalsIgnoreCase(nsecond_child.getBaseName())))
//			{
//				IO.put("Clustering was done previously for : " +ncurr_parent.getName(),2);
//				//remove the .c and .h files from the vector
//				//vTree.removeElement(nfirst_child);
//				//vTree.removeElement(nsecond_child);
//				//vTree.trimToSize();
//			}
//			else 
//				IO.put(ncurr_parent.getName() + "contains files other than " +
//					ncurr.getName().substring(0, ncurr.getName().length()-2) + ".c and " + 
//					ncurr.getName().substring(0, ncurr.getName().length()-2) + ".h ",2);    
//		}
//		else
//			IO.put("Children of : " +ncurr_parent.getName() + " ! = 2 ",2);
//	}
	}
}// end class
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/BodyHeader.java -->

### third_party/acdc/acdc/ClusterLast.java

SHA-256: `81a38aa7824eb487d7aa6db4976f93344af1fe7fad9949dc8bc6f1c9d9aa333e` · 2,134 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/ClusterLast.java 81a38aa7824eb487d7aa6db4976f93344af1fe7fad9949dc8bc6f1c9d9aa333e -->
```java
package acdc;
import java.util.Iterator;
import java.util.Vector;

import javax.swing.tree.DefaultMutableTreeNode;

/**
* This pattern puts together all orphans under one cluster node named
* "orphanContainer", which in turn is inserted under the root of the tree.
*/
public class ClusterLast extends Pattern {
	public ClusterLast(DefaultMutableTreeNode _root) {
		super(_root);
		name = "Cluster Last";
	}

	public void execute() {
		Vector vModified = new Vector();

		if (orphanNumber() != 0) {
			IO.put("Clustering leftover nodes",2);
			// Create a node of type Subsystem which will contain all the remaining unclustered orphans 
			Node nOrphanContainer = new Node("orphanContainer.ss", "Subsystem");
			DefaultMutableTreeNode orphanContainer = new DefaultMutableTreeNode(nOrphanContainer);
			nOrphanContainer.setTreeNode(orphanContainer);
			root.add(orphanContainer);

			Vector allOrphans = orphans();
			Iterator iaO = allOrphans.iterator();

			while (iaO.hasNext())
			{
				Node ncurr = (Node) iaO.next();
				// Change this to an iterator
				//for (int i = 0; i < orphanNumber(); i++) {
				//Node ncurr = (Node) orphans().elementAt(i);
				DefaultMutableTreeNode curr = (DefaultMutableTreeNode) (ncurr.getTreeNode());

				if (!ncurr.isCluster())
				{
					orphanContainer.add(curr);
					IO.put("contain\t\t" + nOrphanContainer.getName() + "\t" + ncurr.getName(),	2);

/* Commented this out. Why do we need to induce edges at this point?
   Uncomment the induceEdges line below, if we need to bring this back in
   
					vModified.add(ncurr);

					Enumeration ecurr = curr.breadthFirstEnumeration();
					while (ecurr.hasMoreElements())
					{
						DefaultMutableTreeNode em = (DefaultMutableTreeNode) ecurr.nextElement();
						vModified.add((Node) em.getUserObject());
					}

					Enumeration emax = curr.breadthFirstEnumeration();
					while (emax.hasMoreElements()) {
						DefaultMutableTreeNode ec =
							(DefaultMutableTreeNode) emax.nextElement();
						vModified.add((Node) ec.getUserObject());
					}
*/
				}
			} // end while
		} //end if

		//induceEdges(vModified, root);
	} //end clusterLast
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/ClusterLast.java -->

### third_party/acdc/acdc/DownInducer.java

SHA-256: `53164fb1b1f74bf3a5fed589e47558b9129f1b96aea771a801a7732a3a2bed12` · 1,165 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/DownInducer.java 53164fb1b1f74bf3a5fed589e47558b9129f1b96aea771a801a7732a3a2bed12 -->
```java
package acdc;
import javax.swing.tree.DefaultMutableTreeNode;
import java.util.*;

public class DownInducer extends Pattern
{
	public DownInducer(DefaultMutableTreeNode _root)
	{
		super(_root);
	}
	
	public void execute() 
	{
		// Remove all but fine-grain clusters from the tree	
		Vector allNodes = allNodes(root);
		Iterator iv = allNodes.iterator();
		
		while (iv.hasNext())
		{
			Node parent = (Node) iv.next();
			DefaultMutableTreeNode tparent = (DefaultMutableTreeNode) parent.getTreeNode();
			if (parent.isCluster())
			{
				Vector subTree = nodeChildren(tparent);
				tparent.removeAllChildren();
				tparent.removeFromParent();
				Iterator is = subTree.iterator();
				boolean hasChildrenFiles = false;
				while (is.hasNext())
				{
					Node child = (Node) is.next();
					if (child.isFile())
					{
						DefaultMutableTreeNode tchild = (DefaultMutableTreeNode) child.getTreeNode();
						tchild.removeAllChildren();
						tparent.add(tchild);
						hasChildrenFiles = true;
					}
				}
				if (hasChildrenFiles) root.add(tparent);
			}
			else
			{
				tparent.removeAllChildren();
			}
		}
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/DownInducer.java -->

### third_party/acdc/acdc/Edge.java

SHA-256: `5505c310f36fde96c83ab364b48e46749512a0f8a111b3a1ab25355a1ad423d2` · 3,413 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/Edge.java 5505c310f36fde96c83ab364b48e46749512a0f8a111b3a1ab25355a1ad423d2 -->
```java
package acdc;
/**
* This class encapsulates information about an Edge object.
* It provides get and set methods for the attributes of this Edge object.
*/
public class Edge 
{
  // Instance variables
  private Node source;
  private Node target;
  private String type;
  private int  weight;
  
 /**
  * Creates an edge initialized with the passed parameters as its source, target,
  * respectively type.
  * @param source   the node which acts as the source of this object
  * @param target   the node which acts as the target of this object
  * @param type	    the type of this object
  */ 
  public Edge(Node source, Node target, String type) 
  {
    this.source = source;
    this.target = target;
    this.type = type;
    weight = 1;
  }
  
 /**
  * Creates an edge initialized with the passed parameters as its source, target,
  * type, respectively weight.
  * @param source   the node which acts as the source of this object
  * @param target   the node which acts as the target of this object
  * @param type	    the type of this object
  * @param weight   the weight of this object 
  */
  public Edge(Node source, Node target, String type, int weight) 
  {
    this.source = source;
    this.target = target;
    this.type = type;
    this.weight = weight;
  }
  
  /**
   * Returns the Node from where <code>this</code> edge originates
   * @return the Node from where this edge originates
   */
   public Node getSource() { return source; }
   
  /**
   * Returns the name of the Node from where <code>this</code> edge originates
   * @return the name of the Node from where this edge originates
   */
   public String getSourceName() { return source.getName(); }
   
  /**
   * Returns the Node towards which <code>this</code> edge is directed
   * @return the Node towards which this edge is directed
   */
   public Node getTarget() { return target; }
   
  /**
   * Returns the name of the Node towards which <code>this</code> edge is directed
   * @return the name of the Node towards which this edge is directed
   */
   public String getTargetName() { return target.getName(); }
   
  /**
   * Returns <code>this</code>  edge's type
   * @return the type of this object
   */
   public String getType() { return type; }
   
  /**
   * Returns <code>this</code> edge's weight value
   * @return the weight value of this edge
   */
   public int getWeight()  { return weight; }
   
  /**
   * Sets the source of <code>this</code> edge 
   * @param source the Node from which this edge originates
   */
   public void setSource(Node source) { this.source = source; }
   
  /**
   * Sets the target of <code>this</code> edge 
   * @param target the Node towards which this edge is directed
   */
   public void setTarget(Node target) { this.target = target; }
   
  /**
   * Sets the type of <code>this</code> edge 
   * @param type the type of this edge
   */
   public void setType(String type) { this.type = type; }
   
  /**
   * Sets the weight of <code>this</code> edge 
   * @param weight the weight value of this edge
   */
   public void setWeight(int weight)  { this.weight = weight; }
  
  /**
   * Returns a string representation of <code>this</code> edge
   * @return type of edge followed by the source's name of this edge followed by the target's name of this edge
   */
   public String toString() 
   {
    return(type + " " + source.getName() + " " + target.getName());
   }
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/Edge.java -->

### third_party/acdc/acdc/FullOutput.java

SHA-256: `b35324f2e0bb164a3de6239b468d593d8ab041cdf664e2a00e85849ceb60d7a6` · 819 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/FullOutput.java b35324f2e0bb164a3de6239b468d593d8ab041cdf664e2a00e85849ceb60d7a6 -->
```java
package acdc;
import javax.swing.tree.DefaultMutableTreeNode;
import java.util.*;

public class FullOutput extends Pattern 
{
	public FullOutput (DefaultMutableTreeNode _root, String _systemName)
	{
		super(_root);
		systemName = _systemName;
	}
	
	private String systemName;
	
	public void execute() 
	{
		// Create an extra root here since OutputHandler ignores the root of the tree
		Node newDummy = new Node (systemName, "Dummy");
		DefaultMutableTreeNode newRoot = new DefaultMutableTreeNode (newDummy);
		newDummy.setTreeNode(newRoot);

		Vector rootChildren = nodeChildren(root);
		Iterator irC = rootChildren.iterator();
		while (irC.hasNext())
		{
			Node n = (Node) irC.next();
			DefaultMutableTreeNode curr = n.getTreeNode();
			newRoot.add(curr);
		}
		root.add(newRoot);
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/FullOutput.java -->

### third_party/acdc/acdc/IO.java

SHA-256: `fa3e9b6302d71b1371411d07ecf12f8ba8478c8ae9c2044606000e499cbde620` · 582 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/IO.java fa3e9b6302d71b1371411d07ecf12f8ba8478c8ae9c2044606000e499cbde620 -->
```java
package acdc;
/*
 * Created on Jul 21, 2003
 *
 * To change the template for this generated file go to
 * Window>Preferences>Java>Code Generation>Code and Comments
 */

/**
 * @author V. Tzerpos
 *
 * To change the template for this generated type comment go to
 * Window>Preferences>Java>Code Generation>Code and Comments
 */
public class IO {
  static int debug_level;
  static void put(String message, int level)
  {
  	if (level <= debug_level) System.out.println(message);
  }
  static void set_debug_level (int level)
  {
  	debug_level = level;
  }
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/IO.java -->

### third_party/acdc/acdc/Inducer.java

SHA-256: `cdd435e297172f68c095f6fe26900ff84564505d5250c8c6d66610f2b8076111` · 149 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/Inducer.java cdd435e297172f68c095f6fe26900ff84564505d5250c8c6d66610f2b8076111 -->
```java
package acdc;
import javax.swing.tree.DefaultMutableTreeNode;

public interface Inducer 
{
	public void induce(DefaultMutableTreeNode root);
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/Inducer.java -->

### third_party/acdc/acdc/InputHandler.java

SHA-256: `b3d523642cdf7c201d40d24880434a67d2a0641df8d7bc9a717696c3c388e499` · 172 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/InputHandler.java b3d523642cdf7c201d40d24880434a67d2a0641df8d7bc9a717696c3c388e499 -->
```java
package acdc;
import javax.swing.tree.DefaultMutableTreeNode;

public interface InputHandler
{
	public void readInput(String inputStr, DefaultMutableTreeNode treeModel);
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/InputHandler.java -->

### third_party/acdc/acdc/Node.java

SHA-256: `d15c76ef1d29bf72782ab48f6ccabdbf5eba73d725ebd7ab6400cbd3f7c4cd47` · 6,729 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/Node.java d15c76ef1d29bf72782ab48f6ccabdbf5eba73d725ebd7ab6400cbd3f7c4cd47 -->
```java
package acdc;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;

import javax.swing.tree.DefaultMutableTreeNode;

/**
* This class encapsulates information about a Node node.
*/
public class Node 
{
    private String name;
    private String type;
    private HashSet sources;
    private HashSet targets;
    private ArrayList incomingEdges;
    private ArrayList outgoingEdges;
    private DefaultMutableTreeNode treeNode;

    public boolean equals(Object o)
    {
    	Node e = (Node) o;
    	return (this.getName()).equals(e.getName());
    }

    /**
     * Creates a node initialized with the passed parameters as its name and type 
     * and sets the remaining attributes to default values.
     *
     * @param name	 the name of this node
     * @param type	 the type of this node
     */
    public Node(String name, String type) 
	{
		this.name = name;
		this.type = type;
		sources = new HashSet();
		targets = new HashSet();
		incomingEdges = new ArrayList();
		outgoingEdges = new ArrayList();
	}
    
    public boolean isCluster()
    {
		if (type.equalsIgnoreCase("cModule") || type.equalsIgnoreCase("Subsystem") ||
			type.equalsIgnoreCase("cSubSystem") || type.equalsIgnoreCase("UnknownContainer"))
			return true;
		else 
			return false;			
    }
    
    public void print()
    {
		IO.put("Node := " + name + ", Type := " + type,2);
	}
    
    public void printLine()
    {
		IO.put("Node := " + name + ", Type := " + type,2);
	}
    
    public void printSources()
    {
	Iterator isources = sources.iterator();
	while(isources.hasNext())
	{    
	    
	}
    }
    
    public void printTargets()
    {
    
	Iterator itargets = targets.iterator();
	while(itargets.hasNext())
	{    
	    Node n = (Node)itargets.next();
	    IO.put("\tTarget of  **** " + name + " **** := " + n.getName() + ", Type := " + n.getType(),2);
	}
    
    }
    
    /**
     * Returns <code>this</code> node's name
     * @return the name of this node
     */
    public String getName() { return name; }
    
	/**
	  * Returns <code>this</code> node's base name, i.e. removes the last dot and anything after it
	  * @return the base name of this node
	  */
	public String getBaseName()
	{
		int pos = name.lastIndexOf('.');
		if (pos == -1)
			return name;
		else
			return name.substring(0,pos);
	}

    /**
     * Returns <code>this</code> node's type
     * @return the type of this node
     */
    public String getType() { return type; }
    
    /**
     * Returns a set of nodes which have edges directed towards <code>this</code> node
     * @return a set of nodes representing the sources of the incoming edges to this node
     */
    public HashSet getSources() { return sources; }
    
    /**
     * Returns a set of nodes towards which the edges of <code>this</code> node are directed
     * @return a set of nodes representing the targets of the outgoing edges of <code>this</code> node
     */
    public HashSet getTargets() { return targets; }
    
    /**
     * Returns a list of the edges which are directed towards <code>this</code> node
     * @return a list of incoming edges to this node
     */
    public ArrayList getIncomingEdges() { return incomingEdges; }
    
    /**
     * Returns a list of the edges which originate from <code>this</code> node
     * @return a list of outgoing edges of this node
     */
    public ArrayList getOutGoingEdges() { return outgoingEdges; }
    
    /**
     * Returns the tree node to which this node is referring 
     * @return the tree node 
     */
    public DefaultMutableTreeNode getTreeNode() { return treeNode; }
    
    
    //public Node getParent() { return parent; }
    //public ArrayList getChildren() { return children; }
    //public void setNodeId(String nodeId) { this.nodeId = nodeId; }
    
    /**
     * Sets the name of <code>this</code> node
     * @param name the name of this node
     */
    public void setName(String name) { this.name = name; }
    
    /**
     * Sets the type of <code>this</code> node
     * @param type the type of this node
     */
    public void setType(String type) { this.type = type; }
    
    /**
     * Sets 
     * @param 
     */
    public void setTreeNode(DefaultMutableTreeNode treeNode)
      { this.treeNode = treeNode; }

    /**
     * Returns true if <code>this</code> node is of type cFile or Unknown 
     * @return true if this node is a file
     */
	public boolean isFile()
	{ 
		if ((type.equals("cFile")) || (type.equals("Unknown")) || (type.equals("File")))
			return true;
		else return false;
	}

     /**
     * Adds an incoming edge to <code>this</code> node. If edge was already an 
     * incoming edge to this node, recalculates its weight. Also, the node from which
     * this edge originates is added to the sources of this node.
     * @param the edge to be added to incomingEdges
     */
    public void addInEdge(Edge e) 
    { 
      Iterator i = incomingEdges.iterator();
      boolean done = false;
      //test if edge e exists in incomingEdges
      //if yes, recalculate its weight, else add edge e to the incomingEdges
      //and add the node from which edge e originates to the sources of this node
      for  ( ; i.hasNext() ; )
      {
	
	Edge j = (Edge)i.next();
	if ((j.getSourceName().equals(e.getSourceName())) && (j.getType().equals(e.getType())))
	{
	  j.setWeight(j.getWeight() + e.getWeight());
	  done = true;
	  break;
	}
      }
      
      if (!done)
      {
	incomingEdges.add(e);
      }
      sources.add(e.getSource());
    }
    
    /**
     * Adds an outgoing edge to <code>this</code> node. If edge was already an 
     * outgoing edge of this node, recalculates its weight. Also, the node towards which this edge
     * is directed is added to the targets of this node.
     * @param the edge to be added to outgoingEdges
     */
    public void addOutEdge(Edge e)
    {
      Iterator i = outgoingEdges.iterator();
      boolean done = false;
      //test if edge e exists in outgoingEdges
      //if yes, recalculate its weight, else add edge e to the outgoingEdges
      //and add the node towards which edge e is directed to the targets of this node
      for  ( ; i.hasNext() ; )
      {
	Edge j = (Edge)i.next();
	if ((j.getTargetName().equals(e.getTargetName())) && (j.getType().equals(e.getType())))
	{
	  j.setWeight(j.getWeight() + e.getWeight());
	  done = true;
	  break;
	}
      }
      if (!done)
      {
	outgoingEdges.add(e);
      }
    targets.add(e.getTarget());
    }
    
    /**
     * Returns a string representation of <code>this</code> node
     * @return name followed by the type of this node
     */
  public String toString() 
  {
    return(name + " " + type);
  }  
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/Node.java -->

### third_party/acdc/acdc/OrphanAdoption.java

SHA-256: `e6310410d6948d580295d6005bdaf31cc2ca84307e7c7992518af523fcb7d32c` · 15,040 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/OrphanAdoption.java e6310410d6948d580295d6005bdaf31cc2ca84307e7c7992518af523fcb7d32c -->
```java
package acdc;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Vector;

import javax.swing.tree.DefaultMutableTreeNode;

/** 
 * This pattern finds and moves children of the root node which are not
 * clusters under the appropriate adoptive cluster-node.
 * An orphan would be placed under the cluster-node with
 * the largest number of children which point to the orphan. 
 * 
 * Tie-breakers are solved by checking the targets of the orphan.
 * 
 * If cluster-nodes A and B are competing for the orphan, that
 * which has the largest number of children being targets of the 
 * orphan, wins it.
 *
 */
public class OrphanAdoption extends Pattern 
{
	public OrphanAdoption(DefaultMutableTreeNode _root)
	{
		super(_root);
		name = "Orphan Adoption";
	}

	public void execute() 
	{
		Vector vModified = new Vector();
		Vector vAdopted;		
		// Run oneRoundForward as many times as the #orphans is decreasing 
		vAdopted = manyRoundsForward();
		
		int on, prevon;
		on = orphanNumber();
		prevon = on + 1;
		while(on < prevon)
		{
			IO.put("Orphan Number: " + on,2);
			prevon = on;
			vAdopted = oneRoundReverse();
			vModified.addAll(vAdopted);
			if (orphanNumber() > 0)
			{
				vAdopted = manyRoundsForward();
				vModified.addAll(vAdopted);
			}
			on = orphanNumber();
		}
		induceEdges(vModified,root);
	}
	
	public Vector oneRoundReverse()
	{
		Vector vReturn = new Vector();
		Vector vRootChildren = nodeChildren(root);
		// Keeps the cluster-nodes which are competing for this orphan 
		Hashtable ht = new Hashtable(10000);
	
	for(int j=0; j<vRootChildren.size();j++)
	{
	   Node ncurr = (Node)vRootChildren.elementAt(j);
	   DefaultMutableTreeNode curr = (DefaultMutableTreeNode)ncurr.getTreeNode();
                              	
		if(!ncurr.isCluster())
		{	
		ht = new Hashtable(10000);
		IO.put("ROA:\torphan =: "+ ncurr.getName(),2);

		//a set of the nodes to which the current orphan points to
		HashSet targets = ncurr.getTargets();
		//if(targets.isEmpty())
			//IO.put("orphan =:"+ncurr.getName()+" has NO TARGETS!");	
		
		Iterator itargets = targets.iterator();
		while (itargets.hasNext())
		{
			Node ncurr_target = (Node)(itargets.next());
			DefaultMutableTreeNode curr_target = 
				(DefaultMutableTreeNode)(ncurr_target.getTreeNode());
			    		
			double counter = 0;
		    
			 /**********************************************************************************    
		      
			  NOTE: retain only targets of the orphan which are clusters <-- only the cluster
					which is lowest in the tree should adopt the orphan,
			 *********************************************************************************/
		    
			//ignore root and its children  as targets of the orphan;
			//also ignore targets of the orphan which are clusters
			if(curr_target.getLevel()>1 && !ncurr_target.isCluster())
			{
			
			
			//IO.put("Rorphan := "+ ncurr.getName() +":::::::::::::: target =: " 
															   //+ncurr_target.getName());
			
			//the parent of this target is competing for the orphan  
			DefaultMutableTreeNode parent =(DefaultMutableTreeNode)curr_target.getParent();
			Node nparent = (Node)parent.getUserObject();			
			//IO.put("::::::: whose parent is :=  ");
			//if parent is orphan or root, do nothing
			if(nparent.getName().equalsIgnoreCase(ncurr.getName()) || nparent.getName().equalsIgnoreCase("ROOT"))
					;
					//IO.put("\nParent of target of orphan " + ncurr.getName() +
						//" is Root or the orphan itself.\n");
			else
			{
				boolean stop = false;
				while(!stop && !nparent.isCluster())
				{
					parent = (DefaultMutableTreeNode)parent.getParent();
					nparent = (Node)parent.getUserObject();
					
					//parent of the source is root or is the orphan
					if(nparent.getName().equalsIgnoreCase(ncurr.getName()) ||
										   nparent.getName().equalsIgnoreCase("ROOT"))
					{
						
						stop = true;
					}
				}
			}
			
			if(nparent.isCluster())
			{
				//dvalues, ivalues, ivalue --> needed for printing only
				//Collection dvalues;
				//Vector ivalues;
				//Double ivalue;
				
				//IO.put(nparent.getName());
				
				//Case1: parent already in the hashtable 
				if(ht.containsKey(nparent))
				{  
				   //counter value get incremented by one unit
					Double i = (Double)ht.get(nparent);
				    
					//IO.put(", iCounter:= " + i);
				    
					counter = i.doubleValue();
					counter++;   
					//remove source with old counter value from the hashtable
					ht.remove(nparent);
					//add the source back to the hashtable with the updated counter value
					ht.put(nparent, new Double(counter));
				    
					//IO.put(", fCounter not new:= "+ counter);
				    
					/*
					IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
					dvalues = ht.values();
					ivalues = new Vector(dvalues);
					for(int j=0; j<ivalues.size(); j++)
					{
						ivalue = (Double)ivalues.elementAt(j);
						IO.put("Value of Hashtable **** " + ivalue.doubleValue());
					}
					IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
					*/
				}
				//Case2: parent was not in the hashtable 
				else
				{   
						counter = 0;
					
					HashSet c_targets = new HashSet();
					Enumeration ps = parent.breadthFirstEnumeration();
					while(ps.hasMoreElements())
					{
						DefaultMutableTreeNode ps_curr = (DefaultMutableTreeNode)ps.nextElement();
						Node nps_curr = (Node)ps_curr.getUserObject();
						c_targets= nps_curr.getTargets();
						if(c_targets.contains(ncurr))
						{	counter = counter + 0.000001;
							//IO.put(", Counter:= "+ counter);
						}	
					}
					
					//add parent to the hashtable with a counter value incremented by one more unit
					ht.put(nparent, new Double(++counter));
					//IO.put(", Counter:= "+ counter);
					
					/*
					IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
					dvalues = ht.values();
					ivalues = new Vector(dvalues);
						for(int i=0; i<ivalues.size(); i++)
						{
							ivalue = (Double)ivalues.elementAt(i);
							IO.put("Value of Hashtable **** " + ivalue.doubleValue());
						}
						IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
					*/
				}
			}
					
				}
				
		}// end while
		
		if(ht.isEmpty())
			IO.put("\tNOT\t adopted",2);
		//the hashtable now contains all the candidate nodes for adopting the orphan
		//the node in the hashtable with the highest counter value will get the orphan
		if(!ht.isEmpty())
		{	
			double max_value = 0;
			Node max_key = new Node("faraz","oana");
		    
			/*
			Collection cvalues = ht.values();
			Vector values = new Vector(cvalues);
			for(int i=0; i<values.size(); i++)
			{
				Double value = (Double)values.elementAt(i);
				IO.put("Value of Hashtable **** " + value.doubleValue());
			}
			*/
		    
			Enumeration keys = ht.keys();
			while (keys.hasMoreElements())
			{
			Node curr_key =  (Node)keys.nextElement();
			//IO.put("Hashtable contains: ");
			//curr_key.print();
			
			Double curr_value = (Double)ht.get(curr_key);
			//IO.put(", Value := " + curr_value.doubleValue());
			
			
			if(curr_value.doubleValue() >= max_value)
			{
				max_value = curr_value.doubleValue() ;
				max_key = curr_key;
			}
		    	
			}
		    
			DefaultMutableTreeNode max = (DefaultMutableTreeNode)(max_key.getTreeNode());
			max.add(curr);
		 
			Enumeration emax = curr.breadthFirstEnumeration();
			while(emax.hasMoreElements())
			{
				DefaultMutableTreeNode ec = (DefaultMutableTreeNode)emax.nextElement();
			if(!vReturn.contains((Node)ec.getUserObject()))
				vReturn.add((Node)ec.getUserObject());
			}
		  
			IO.put("\twas adopted by ***\t" + max_key.getName(),2);
		   
		}
		}// end if     
	}// end while		
	
	return vReturn;
	}
	
	public Vector manyRoundsForward()
	{
		Vector result = new Vector();
		Vector vAdopted;		
		// Run oneRoundForward as many times as the #orphans is decreasing 
		do
		{
			vAdopted = oneRoundForward();
			IO.put("Before "+vAdopted.size(),2);
			result.addAll(vAdopted);
			IO.put("After "+vAdopted.size()+"",2);
		}
		while(vAdopted.size() > 0);
		return result;
	}
	
	public Vector oneRoundForward ()
	{
		Vector vReturn = new Vector();
		//vector will contain the orphans adopted
		Vector vRootChildren = nodeChildren(root);

		// Hashtable keeps track of the nodes competing for the current orphan 
		Hashtable ht = new Hashtable(10000);

		for (int j = 0; j < vRootChildren.size(); j++) 
		{
			Node ncurr = (Node) vRootChildren.elementAt(j);
			DefaultMutableTreeNode curr = (DefaultMutableTreeNode) ncurr.getTreeNode();

			if (!ncurr.isCluster()) 
			{
				//begin with an empty hashtable for each orphan
				ht = new Hashtable(10000);
				IO.put("OA:\torphan  =: " + ncurr.getName(), 2);

				//sources = set of nodes which point to the current orphan 
				HashSet sources = ncurr.getSources();
				//ncurr.printSources();
				//if(sources.isEmpty())
				//IO.put("orphan =:"+ncurr.getName()+" has NO SOURCES!");
				Iterator isources = sources.iterator();
				//iterate through the sources

				while (isources.hasNext()) 
				{
					Node ncurr_source = (Node) (isources.next());
					//IO.put("\tSource =: " +ncurr_source.getName());
					DefaultMutableTreeNode curr_source =
						(DefaultMutableTreeNode) (ncurr_source.getTreeNode());

					double counter = 0;

					/**********************************************************************************    
					  
					  NOTE: retain only sources of the orphan which are clusters <-- only the cluster
					        which is lowest in the tree should adopt the orphan,
					 *********************************************************************************/

					//ignore root and its children  as sources of the orphan;

					//      --> we ignore sources of the orphan which are clusters
					if (curr_source.getLevel() > 1 && !ncurr_source.isCluster()) 
					{
						//IO.put("orphan := "+ ncurr.getName() +":::::::::::::: source =: " +ncurr_source.getName());

						//the parent of this source is competing for the orphan  
						DefaultMutableTreeNode parent =
							(DefaultMutableTreeNode) curr_source.getParent();
						Node nparent = (Node) parent.getUserObject();
						//IO.put("::::::: whose parent is :=  ");

						//if parent is orphan or root, do nothing
						if (nparent.getName().equalsIgnoreCase(ncurr.getName())
							|| nparent.getName().equalsIgnoreCase("ROOT"));
						else {
							boolean stop = false;
							while (!stop && !nparent.isCluster()) {
								parent =
									(DefaultMutableTreeNode) parent.getParent();
								nparent = (Node) parent.getUserObject();

								//parent of the source is root or is the orphan
								if (nparent.getName().equalsIgnoreCase(ncurr.getName())
									|| nparent.getName().equalsIgnoreCase("ROOT")) {

									stop = true;
								}
							}
						}

						if (nparent.isCluster()) {
							//dvalues, ivalues, ivalue --> needed for printing only
							//Collection dvalues;
							//Vector ivalues;
							//Double ivalue;

							//IO.put(nparent.getName());
							//Case1: parent already in the hashtable 
							if (ht.containsKey(nparent)) {
								//counter value get incremented by one unit
								Double i = (Double) ht.get(nparent);
								//IO.put(", iCounter:= " + i);
								counter = i.doubleValue();
								counter++;
								//remove source with old counter value from the hashtable
								ht.remove(nparent);
								//add the source back to the hashtable with the updated counter value
								ht.put(nparent, new Double(counter));
								//IO.put(", fCounter not new:= "+ counter);

								/*
								IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
								dvalues = ht.values();
								ivalues = new Vector(dvalues);
								for(int j=0; j<ivalues.size(); j++)
								{
									ivalue = (Double)ivalues.elementAt(j);
									IO.put("Value of Hashtable **** " + ivalue.doubleValue());
								}
								IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
								*/
							}
							//Case2: parent not in the hashtable
							else {
								counter = 0;
								HashSet c_sources = new HashSet();
								Enumeration ps =
									parent.breadthFirstEnumeration();
								ps.nextElement();
								//don't count the parent itself which surely points to curr due to edge induction
								while (ps.hasMoreElements()) {
									DefaultMutableTreeNode ps_curr =
										(DefaultMutableTreeNode) ps
											.nextElement();
									Node nps_curr =
										(Node) ps_curr.getUserObject();
									c_sources = nps_curr.getSources();
									if (c_sources.contains(ncurr)) {
										counter = counter + 0.000001;
										//IO.put(", Counter:= "+ counter);
									}
								}

								//add parent to the hashtable with a counter value incremented by one more unit
								ht.put(nparent, new Double(++counter));
								//IO.put(", Counter:= "+ counter);

								/*
								IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
								dvalues = ht.values();
								ivalues = new Vector(dvalues);
								    for(int i=0; i<ivalues.size(); i++)
								    {
										ivalue = (Double)ivalues.elementAt(i);
										IO.put("Value of Hashtable **** " + ivalue.doubleValue());
								    }
								    IO.put("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^");
								*/
							}
						}
						//else
						//IO.put("");		
					}

				} // end while

				if (ht.isEmpty())
					IO.put("\tNOT\t adopted", 2);
				//the hashtable now contains all the candidate nodes for adopting the orphan
				//the node in the hashtable with the highest value will get the orphan
				if (!ht.isEmpty()) {
					double max_value = 0;
					Node max_key = new Node("faraz", "oana");

					/*
					Collection cvalues = ht.values();
					Vector values = new Vector(cvalues);
					for(int i=0; i<values.size(); i++)
					{
						Double value = (Double)values.elementAt(i);
						IO.put("Value of Hashtable **** " + value.doubleValue());
					}
					*/

					Enumeration keys = ht.keys();
					while (keys.hasMoreElements()) {
						Node curr_key = (Node) keys.nextElement();
						//IO.put("Hashtable contains: ");
						//curr_key.print();

						Double curr_value = (Double) ht.get(curr_key);
						//IO.put(", Value := " + curr_value.doubleValue());

						if (curr_value.doubleValue() >= max_value) {
							max_value = curr_value.doubleValue();
							max_key = curr_key;
						}

					}

					DefaultMutableTreeNode max =
						(DefaultMutableTreeNode) (max_key.getTreeNode());
					max.add(curr);

					Enumeration emax = curr.breadthFirstEnumeration();
					while (emax.hasMoreElements()) {
						DefaultMutableTreeNode ec =
							(DefaultMutableTreeNode) emax.nextElement();
						if (!vReturn.contains((Node) ec.getUserObject()))
							vReturn.add((Node) ec.getUserObject());
					}

					IO.put("\twas adopted by ***\t" + max_key.getName(), 2);

				}
			} // end if     
		} // end while

		return vReturn;
	} //end execute
} //end class
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/OrphanAdoption.java -->

### third_party/acdc/acdc/OutputHandler.java

SHA-256: `e05f26491990a1fdc5a0c76ae344298ef8cfba9933ef83a24d4b03b29adfc0a0` · 172 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/OutputHandler.java e05f26491990a1fdc5a0c76ae344298ef8cfba9933ef83a24d4b03b29adfc0a0 -->
```java
package acdc;
import javax.swing.tree.DefaultMutableTreeNode;

public interface OutputHandler
{
	public void writeOutput(String outputName, DefaultMutableTreeNode root);
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/OutputHandler.java -->

### third_party/acdc/acdc/Pattern.java

SHA-256: `bc97e84f414d8778c372edb92e0a7ccbe2aee4b8e740639a07e1d2f7b2bf9920` · 4,329 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/Pattern.java bc97e84f414d8778c372edb92e0a7ccbe2aee4b8e740639a07e1d2f7b2bf9920 -->
```java
package acdc;
import java.util.*;
import javax.swing.tree.*;

public abstract class Pattern {
	public Pattern(DefaultMutableTreeNode _root)
	{
		root = _root;
		name = "";
	}
	
	protected DefaultMutableTreeNode root;
	
	protected String name;
	
	public String getName()
	{
		return name;
	}

	protected abstract void execute();

	protected Vector nodeChildren(DefaultMutableTreeNode node) 
	{
		Vector result = new Vector();
		Enumeration children = node.children();
		while (children.hasMoreElements()) 
		{
			DefaultMutableTreeNode curr2 = (DefaultMutableTreeNode) children.nextElement();
			Node ncurr2 = (Node) curr2.getUserObject();
			result.add(ncurr2);
		}
		return result;
	}
	
	protected Vector orphans()
	{
		Vector result = new Vector();
		Vector rootChildren = nodeChildren(root);
		Iterator iv = rootChildren.iterator();

		while (iv.hasNext())
		{
			Node curr = (Node) iv.next();
			if (!curr.isCluster())
				result.add(curr);
		}
		return result;
	}

	protected int orphanNumber()
		{
			Vector rootChildren = nodeChildren(root);
			Iterator iv = rootChildren.iterator();
			int count = 0;
			while (iv.hasNext())
			{
				Node curr = (Node) iv.next();
				if (!curr.isCluster())
					count ++;
			}
			return count;
		}

	public static Vector allNodes(DefaultMutableTreeNode root)
	{
		Vector result = new Vector(); // will contain all nodes in the tree
		Enumeration treeNodes = root.breadthFirstEnumeration();
		// The first node in the enumeration is the root. We skip it over.
		DefaultMutableTreeNode curr = (DefaultMutableTreeNode) treeNodes.nextElement();
		while(treeNodes.hasMoreElements())
		{
			curr = (DefaultMutableTreeNode)treeNodes.nextElement();
			Node ncurr = (Node)curr.getUserObject();
			result.add(ncurr);
		}
		return result;
	}
	
	public static void induceEdges(Vector v, DefaultMutableTreeNode root) 
	{
		IO.put("The following " + v.size() + " nodes were selected for edge induction", 2);
		for (int m = 0; m < v.size(); m++)
		{
			Node ncurr = (Node) v.elementAt(m);
			IO.put(ncurr.getName(), 2);
			HashSet outNodes = (HashSet) ncurr.getTargets().clone();
			//IO.put("\n");
			//traverse the set of target nodes of the current node
			Iterator ioN = outNodes.iterator();
			while (ioN.hasNext()) {
				//traverse the nodes from the root to the current   
				//target node creating edges 
				Node across = (Node) ioN.next();
				DefaultMutableTreeNode tacross = across.getTreeNode();
				TreeNode[] path = tacross.getPath();
				for (int i = 0; i < path.length; i++) {
					TreeNode k = path[i];
					DefaultMutableTreeNode j = (DefaultMutableTreeNode) k;
					Node nj = (Node) j.getUserObject();
					//IO.put("EdgeInduction.java\t\tTarget " + nj.getName());
					//don't create induced edges for the root or circular edges 
					if (!j.isRoot()) {
						Edge e = new Edge(ncurr, nj, "induced");
						IO.put("\tInduced edge from "	+ ncurr.getName() + " to " + nj.getName(), 2);
						nj.addInEdge(e);
						ncurr.addOutEdge(e);
					}
				}
			}
		}

		for (int j = 0; j < v.size(); j++) {

			Node ncurr2 = (Node) v.elementAt(j);
			IO.put(ncurr2.getName(), 2);
			//keep a set of the sources nodes of the current node
			HashSet outNodes2 = (HashSet) ncurr2.getSources().clone();

			//traverse the set of target nodes of the current node
			Iterator ioN2 = outNodes2.iterator();
			while (ioN2.hasNext()) {
				//IO.put("\n");
				//traverse the nodes from the root to
				//the current target node creating edges
				Node across2 = (Node) ioN2.next();
				DefaultMutableTreeNode tacross2 = across2.getTreeNode();
				TreeNode[] path2 = tacross2.getPath();
				for (int i = 0; i < path2.length; i++) {
					TreeNode k2 = path2[i];
					DefaultMutableTreeNode j2 = (DefaultMutableTreeNode) k2;
					Node nj2 = (Node) j2.getUserObject();
					//IO.put("EdgeInduction.java\t\tSource " + nj2.getName());
					//current node is in the path of current source
					//therefore don't create any edges
					//if(nj2.getName().equalsIgnoreCase(ncurr.getName()))
					//{

					//}else{
					//don't create induced edges for
					//the root
					if (!j2.isRoot()) {
						Edge e2 = new Edge(nj2, ncurr2, "induced");
						IO.put("\tInduced edge from " + nj2.getName() + " to " + ncurr2.getName(), 2);
						nj2.addOutEdge(e2);
						ncurr2.addInEdge(e2);
					}
				}
			}
		}
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/Pattern.java -->

### third_party/acdc/acdc/RSFOutput.java

SHA-256: `f38ee1c268b7c78cd7b5732ad3990cfe1afc11d8cc55eb5b83cd8af39d304fc0` · 1,222 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/RSFOutput.java f38ee1c268b7c78cd7b5732ad3990cfe1afc11d8cc55eb5b83cd8af39d304fc0 -->
```java
package acdc;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Enumeration;

import javax.swing.tree.DefaultMutableTreeNode;

/**
* This class has one method which creates an RSF file.
* 
* The string representation of the output is of the format: 
*
* contain parent_node node
*
*/
public class RSFOutput implements OutputHandler 
{
	public void writeOutput(String outputName, DefaultMutableTreeNode root) 
	{
		PrintWriter out = null;
		try 
		{
			out = new PrintWriter(new BufferedWriter(new FileWriter(outputName)));
		} 
		catch (IOException e) 
		{
			System.err.println(e.getMessage());
		}

		Node ncurr, nj, ni, np;
		DefaultMutableTreeNode curr, i, j, pi;

		Enumeration allNodes = root.breadthFirstEnumeration();

		// Avoid output for the root node
		i = (DefaultMutableTreeNode) allNodes.nextElement();

		while (allNodes.hasMoreElements()) 
		{
			i = (DefaultMutableTreeNode) allNodes.nextElement();

			ni = (Node) i.getUserObject();

			pi = (DefaultMutableTreeNode) i.getParent();

			np = (Node) pi.getUserObject();

			if (pi != root) out.println("contain " + np.getName() + " " + ni.getName());
		}
		out.close();
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/RSFOutput.java -->

### third_party/acdc/acdc/Sortable.java

SHA-256: `49e1eaf0d25446af39b659b3388ebb0ff56a5a14a799a23990cef039107effbe` · 840 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/Sortable.java 49e1eaf0d25446af39b659b3388ebb0ff56a5a14a799a23990cef039107effbe -->
```java
package acdc;
public class Sortable implements Comparable 
{
private  Comparable key = "";
private  Object o = null;

/************************************************/
public Sortable(Comparable key , Object o )
  {
  this.key = key;
  this.o = o;
  }

/************************************************/
public void setKey ( Comparable key )
  {
  this.key = key;
  }

/************************************************/
public Comparable getKey()
  {
  return ( key );
  }

/************************************************/
public void setObject ( Object o )
  {
  this.o = o;
  }

/************************************************/
public Object getObject()
  {
  return ( o );
  }

/************************************************/
public int compareTo ( Object o )
  {
  return ( key.compareTo ( ((Sortable) o).getKey() ) );
  }  
}

```
<!-- END_FULL_SOURCE third_party/acdc/acdc/Sortable.java -->

### third_party/acdc/acdc/SubGraph.java

SHA-256: `cd12e4296c0b3e281742b8ef41c91f77db669f8ec3ed466968765c1f8201f2f7` · 12,055 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/SubGraph.java cd12e4296c0b3e281742b8ef41c91f77db669f8ec3ed466968765c1f8201f2f7 -->
```java
package acdc;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Enumeration;
import java.util.HashSet;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Vector;
import javax.swing.tree.DefaultMutableTreeNode;

/**
 * @author V. Tzerpos
 *
 * Clusters the children of the root based on their dependencies
 */
public class SubGraph extends Pattern {
	private int clusterSize;

	public SubGraph(DefaultMutableTreeNode _root, int size) {
		super(_root);
		clusterSize = size;
		name = "Subgraph Dominator";
	}

	public void execute() {
		Vector vModified = new Vector();
		Vector vRootChildren = nodeChildren(root);

		//************************************************************************
		// Note: The nodes to be clustered are the children of the root only. 
		//       Their corresponding subtree should not be modified!             
		//************************************************************************

		HashSet setOfTargets = new HashSet();

		//put nodes to be clustered together with their corresponding number of targets in a HashTable
		Hashtable ht = new Hashtable(10000);

		int counter = 0; // keeps track of #targets per node

		Iterator ivRC = vRootChildren.iterator();
		while (ivRC.hasNext())
		{
			Node ncurr = (Node) ivRC.next();
			setOfTargets = new HashSet(); //reset

			setOfTargets.add((DefaultMutableTreeNode) ncurr.getTreeNode());
			setOfTargets = findTargets(setOfTargets, vRootChildren);

			counter = 0; //reset

			Iterator ihs = setOfTargets.iterator();
			//count only targets which are children of root
			while (ihs.hasNext()) {
				DefaultMutableTreeNode c = (DefaultMutableTreeNode) ihs.next();
				Node n = (Node) c.getUserObject();

				if (vRootChildren.contains(n)) {
					//IO.put(n.getName()+" is in vRootChildren");
					counter++;
				}
			}
			ht.put(ncurr, new Integer(counter));
		}

		//sort ht in increasing order

		ArrayList my_array = new ArrayList();
		for (Enumeration e = ht.keys(); e.hasMoreElements();) {
			Node curr_key = (Node) e.nextElement();
			Integer curr_value = (Integer) ht.get(curr_key);

			// build a sortable object with the two pieces of information
			Sortable s_before = new Sortable(curr_value, curr_key);

			// add the sortable object to the sarray
			my_array.add(s_before);
		}
		Collections.sort(my_array);

		for (int i = 0; i < my_array.size(); i++) {

			Sortable s_print = (Sortable) my_array.get(i);

			Node object_key = (Node) s_print.getObject();

			Integer integer_object = (Integer) s_print.getKey();

			IO.put("Node = " + object_key.getName()	+
			       " , Type := "	+ object_key.getType() +
			       " , Targets = " + integer_object, 2);

		}

		Node tentativeDominator;
		int next_index = 0;
		boolean found;
		
		// This is where the big loop begins
		
		while (!ht.isEmpty()) {
			//some nodes (identified below as covered set nodes) might be removed from
			//the hashtable so we want to make sure that our ArrayList is also updated
			do {
				Sortable s_after = (Sortable) my_array.get(next_index++);
				tentativeDominator = (Node) s_after.getObject();
				//while hashtable doesn't contain it, skip over current node to the next one
				if (ht.containsKey(tentativeDominator))
					found = true;
				else
					found = false;
			} while (!found);

			DefaultMutableTreeNode tentativeDominatorTreeNode = (DefaultMutableTreeNode) (tentativeDominator.getTreeNode());

			IO.put("**************************", 2);
			IO.put("Dominator " + tentativeDominator, 2);
			HashSet cS = coveredSet(tentativeDominatorTreeNode, vRootChildren);
			if (cS.size() == 1)
			{
				ht.remove(tentativeDominator);
			}
			else //coveredSet returned tentativeRoot and its set of dominated nodes
			{
				// max cluster size allowed is clusterSize!!

				DefaultMutableTreeNode curr_cS;
				Node ncurr_cS;
				if (cS.size() < clusterSize)
				{
					Iterator ic = cS.iterator();
					while (ic.hasNext())
					{
						curr_cS = (DefaultMutableTreeNode) ic.next();
						ncurr_cS = (Node) curr_cS.getUserObject();
						//IO.put("Covered Set Node ***" + ncurr_cS.getName() + " ,Type := " +
						// ncurr_cS.getType() + " was removed from hashtable!!!");
						ht.remove(ncurr_cS);
					}
				}
				else //if cS has more than clusterSize elements, attempt deeper clustering
				{
					ht.remove(tentativeDominator);
				}

				// Create a new subsystem node
				Node ssNode = new Node(tentativeDominator.getBaseName() + ".ss", "Subsystem");
				if (!vModified.contains(ssNode))
				{
					vModified.add(ssNode);
				}

				IO.put("Cluster Node " + ssNode.getName() + " was created and contains :", 2);

				DefaultMutableTreeNode ssTreeNode = new DefaultMutableTreeNode(ssNode);
				ssNode.setTreeNode(ssTreeNode);

				// Find the most immediate common ancestor of all elements in the covered set
				Iterator icS = cS.iterator();
				DefaultMutableTreeNode ancestor = (DefaultMutableTreeNode) icS.next();
				ancestor = (DefaultMutableTreeNode) ancestor.getSharedAncestor((DefaultMutableTreeNode) icS.next());
				while (icS.hasNext())
				{
					ancestor = (DefaultMutableTreeNode) ancestor.getSharedAncestor((DefaultMutableTreeNode) icS.next());
				}

				// Insert the new node just below the ancestor
				Iterator ics2 = cS.iterator();
				HashSet nodesToMove = new HashSet();

				IO.put("Ancestor :=  " + ((Node) (ancestor.getUserObject())).getName(), 2);
				int numOfElementsInPath = 0;
				boolean continueLoop = true;
				while (ics2.hasNext() && continueLoop) {

					DefaultMutableTreeNode nnn = (DefaultMutableTreeNode) ics2.next();
					Enumeration path = nnn.pathFromAncestorEnumeration(ancestor);
					numOfElementsInPath = 0;
					while (path.hasMoreElements()) {
						path.nextElement();
						numOfElementsInPath++;
					}
					//IO.put("numOfElementsInPath := " 
					// + numOfElementsInPath);
					//if ancestor belongs to covered set,only ancestor should be moved
					if (numOfElementsInPath == 1) {
						nodesToMove.clear();
						nodesToMove.add(ancestor);
						continueLoop = false;
						IO.put("Ancestor belongs to the covered set!", 2);
					} else {
						path = nnn.pathFromAncestorEnumeration(ancestor);

						//firstNode is same as ancestor!
						DefaultMutableTreeNode firstNode =
							(DefaultMutableTreeNode) path.nextElement();

						DefaultMutableTreeNode secondNode =
							(DefaultMutableTreeNode) path.nextElement();
						nodesToMove.add(secondNode);
					}

				}

				//new node contains all the nodes in covered set and others too
				Iterator intm = nodesToMove.iterator();
				while (intm.hasNext()) {
					DefaultMutableTreeNode nextToMove =
						(DefaultMutableTreeNode) intm.next();
					if (!nextToMove.equals(ssTreeNode))
						ssTreeNode.add(nextToMove);

					//there are no outside sources for coveredSet nodes, threfore edgeInduction is only needed for the 
					//newly created cluster node 

					Enumeration ecurr = nextToMove.breadthFirstEnumeration();
					while (ecurr.hasMoreElements()) {

						DefaultMutableTreeNode em =
							(DefaultMutableTreeNode) ecurr.nextElement();
						if (!vModified.contains((Node) em.getUserObject()))
							vModified.add((Node) em.getUserObject());
					}

					IO.put(" Moved:\t" + ((Node) (nextToMove.getUserObject())).getName(), 2);
				}

				if (ancestor == root) {
					ancestor.add(ssTreeNode);

				} else {
					//only child is the ancestor
					if (ssTreeNode.equals(ancestor)) {
						IO.put("Opa", 2);

						//DefaultMutableTreeNode parentOfAncestor = 
						//(DefaultMutableTreeNode)ancestor.getParent();
						//IO.put("Parent of Ancestor :=  " 
						//+ ((Node)(parentOfAncestor.getUserObject())).getName()) ;

						// if ancestor belongs to covered set, former parent 
						//of ancestor (current parent of ancestor is ssTreeNode) 
						// should become parent of ssTreeNode
						//parentOfAncestor.add(ssTreeNode);
					} else {
						ancestor.add(ssTreeNode);

					}

				}

			} //end else
			//loop++;
		} //end while
		//return -1;
		induceEdges(vModified, root);
	} //end execute

	static void printCoveredSet(DefaultMutableTreeNode domin, Vector vTree) {
		IO.put(
			"**************************************************************",
			2);
		HashSet cS = coveredSet(domin, vTree);
		Iterator icS = cS.iterator();
		while (icS.hasNext()) {
			DefaultMutableTreeNode curr = (DefaultMutableTreeNode) icS.next();
			Node ncurr = (Node) curr.getUserObject();
			IO.put(
				"\tCovered Set Node: **** "
					+ ncurr.getName()
					+ " , Type := "
					+ ncurr.getType(),
				2);
		}

		HashSet tS = findTargets(cS, vTree);
		Iterator itS = tS.iterator();
		while (itS.hasNext()) {
			DefaultMutableTreeNode curr1 = (DefaultMutableTreeNode) itS.next();
			Node ncurr1 = (Node) curr1.getUserObject();
			IO.put(
				"\t** Target of covered set:= "
					+ ncurr1.getName()
					+ " , Type := "
					+ ncurr1.getType(),
				2);

			HashSet sS = findSources(curr1, vTree);
			Iterator isS = sS.iterator();
			while (isS.hasNext()) {
				DefaultMutableTreeNode curr2 =
					(DefaultMutableTreeNode) isS.next();
				Node ncurr2 = (Node) curr2.getUserObject();
				IO.put(
					"\t\tIts source := "
						+ ncurr2.getName()
						+ " , Type := "
						+ ncurr2.getType(),
					2);
			}
		}
	}

	/**
	* Returns the HashSet containing the passed arg, called "dominator node", and 
	* the set of its dominated nodes, N = n(i), i:1,2,...m,  which have 
	* the following properties:
	*
	* 1. there exists a path from tentativeRoot to every n(i)
	* 2. for any node v such that there exists a path from v to any n(i), either 
	*    tentativeRoot is in that path or v is one of n(i)
	*/
	private static HashSet coveredSet(
		DefaultMutableTreeNode tentativeRoot,
		Vector vTree) {
		HashSet result = new HashSet();
		result.add(tentativeRoot);

		HashSet covered, falseOnes, fathers, both;

		do {
			covered = findTargets(result, vTree);
			covered.removeAll(result);
			falseOnes = new HashSet();
			do {
				both = (HashSet) covered.clone();
				both.addAll(result);
				Iterator ic = covered.iterator();
				while (ic.hasNext()) {
					DefaultMutableTreeNode curr =
						(DefaultMutableTreeNode) ic.next();
					fathers = findSources(curr, vTree);
					if (!both.containsAll(fathers))
						falseOnes.add(curr);
				}

			}
			while (covered.removeAll(falseOnes));
			// will exit if covered doesn't change
		}
		while (result.addAll(covered)); // will exit if result doesn't change
		return result;
	}

	/**
	* Returns a HashSet containing the target nodes of all the
	* items in the passed HashSet parameter.
	*/
	private static HashSet findTargets(
		HashSet source,
		Vector vRootChildren) // was vTree
	{

		HashSet allTargets = new HashSet();

		//iterate thorough the passed HashSet    
		Iterator iS = source.iterator();
		while (iS.hasNext()) {
			DefaultMutableTreeNode curr = (DefaultMutableTreeNode) iS.next();
			Node ncurr = (Node) curr.getUserObject();

			//get the targets of the current node in the iteration      
			HashSet targets = ncurr.getTargets();

			//iterate through these targets adding each to the HashSet 'targets'
			Iterator iT = targets.iterator();
			while (iT.hasNext()) {
				Node n = (Node) iT.next();

				if (vRootChildren.contains(n)) // was !vTree
					{
					DefaultMutableTreeNode t = n.getTreeNode();
					allTargets.add(t);
				}
			}
		}
		return allTargets;
	}

	/**
	* Returns a HashSet containing the sources of the passed node parameter.
	*/
	private static HashSet findSources (DefaultMutableTreeNode target, Vector vRootChildren)
	{
		HashSet allSources = new HashSet();

		//get sources of the passed node
		Node ntarget = (Node) target.getUserObject();
		HashSet sources = ntarget.getSources();

		//iterate through the sources of the passed node
		//and add them to the HashSet called 'sources'
		Iterator iS = sources.iterator();
		while (iS.hasNext()) {
			Node n = (Node) iS.next();
			if (vRootChildren.contains(n))
				{
				DefaultMutableTreeNode t = n.getTreeNode();
				allSources.add(t);
			}
		}
		return allSources;
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/SubGraph.java -->

### third_party/acdc/acdc/TAInput.java

SHA-256: `40b2d1b6d3838b87f5522e082375877faf25d268b7833d8b85b6e7bc0e508229` · 11,256 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/TAInput.java 40b2d1b6d3838b87f5522e082375877faf25d268b7833d8b85b6e7bc0e508229 -->
```java
package acdc;
import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.Enumeration;
import java.util.StringTokenizer;

import javax.swing.tree.DefaultMutableTreeNode;

/**
* This class creates a tree from the info passed 
* by the input file.
*/
public class TAInput implements InputHandler
{
	public void readInput(String inputStr, DefaultMutableTreeNode treeModel)
	{
		String str, firstTok, secondTok, thirdTok;
		IO.put("Reading input...",1);
		try 
		{
			BufferedReader in = new BufferedReader(new FileReader(inputStr));
			str = in.readLine();
			if (str != null)
				str = str.trim();
			else
			{
				// Abort if input file was empty
				IO.put("Empty input file!",1);
				System.exit(0);
			}
	      
			// Skip the lines between "Scheme Tuple" and "Fact Tuple"
			if (str.equals("SCHEME TUPLE :"))
				do
				{
					str = in.readLine();
					str = str.trim();
				} while (!str.equals("FACT TUPLE :"));
	      
			// Skip "Fact Tuple:"
			if (str.equals("FACT TUPLE :")) 
			{
				str = in.readLine();
				str = str.trim();
			}
			
			// Following lines up to end of file or to "Fact Attribute" should contain 3 tokens per line
			do
			{
				StringTokenizer strTok = new StringTokenizer(str);
				
				// If encountering a line which doesn't contain 3 tokens per line, abort with a message
				if(strTok.countTokens() != 3)
				{
					IO.put("Syntax error in input file!",0);
					IO.put("The following tuple contains " + strTok.countTokens() + " tokens:",0);
					IO.put(str,0);
					IO.put("Aborting...",0);
					System.exit(0);
				}

				firstTok  = strTok.nextToken(); //type of relation
				secondTok = strTok.nextToken(); 
				thirdTok  = strTok.nextToken(); 

				/******************************************************************************
				      CASE 1: first token in the line is  "$INSTANCE"
				 ******************************************************************************/
				if (firstTok.equals("$INSTANCE"))
				{ 
					//secondTok <-- name of a node in the tree
					//thirdTok  <-- type of a node in the tree

					// If secondTok has been instantiated before, abort with a message
					DefaultMutableTreeNode root = (DefaultMutableTreeNode)treeModel.getRoot();
					Enumeration allNodes = root.depthFirstEnumeration();
					while (allNodes.hasMoreElements())
					{
						Object i = allNodes.nextElement();
						DefaultMutableTreeNode j = (DefaultMutableTreeNode)i;
						Node n = (Node)j.getUserObject();
						if (n.getName().equals(secondTok))
						{
							IO.put("Syntax error in input file!",0);
							IO.put("Two instances of " + secondTok,0);
							IO.put("Aborting...",0);
							System.exit(0);
						}
					}
					IO.put("TAInput.java:\t$INSTANCE Will create node " + secondTok,2);

					// Create a node and instantiate it with the given name and type
					Node n = new Node(secondTok, thirdTok);
					// Insert the node in the tree under the root
					DefaultMutableTreeNode tn = new DefaultMutableTreeNode(n);
					n.setTreeNode(tn);
					root.add(tn);
				}
				
		/******************************************************************************
		      CASE 2: first token in the line is  "contain"
		*****************************************************************************/
		else if (firstTok.equals("contain"))
		{
		  //secondTok <-- name of a node (maybe) in the tree
		  //thirdTok  <-- name of a node (maybe) in the tree

		  //traverse the tree
		  DefaultMutableTreeNode root = 
					 (DefaultMutableTreeNode)treeModel.getRoot();
		  Enumeration allNodes = root.depthFirstEnumeration();
		  DefaultMutableTreeNode tn1 = null;
		  DefaultMutableTreeNode tn2 = null;
		  
		  //check if the tree already contains a node 
		  //with the same name as secondTok or thirdTok
		  while (allNodes.hasMoreElements())
		  {
		    Object i = allNodes.nextElement();
		    DefaultMutableTreeNode j = (DefaultMutableTreeNode)i;
		    Node n = (Node)j.getUserObject();
		    if (n.getName().equals(secondTok)) tn1 = j;
		    if (n.getName().equals(thirdTok)) tn2 = j;
		  }
		  //if secondTok corresponding node was not found as part of the tree
		  //create a node and add it under root
		  if (tn1 == null) 
		  {
        	    Node n1 = new Node(secondTok, "UnknownContainer");
        	    IO.put("Container of unknown type: " + secondTok + ". Assumed to be a cluster", 2);
		    tn1 = new DefaultMutableTreeNode(n1);
        	    n1.setTreeNode(tn1);
		    root.add(tn1);
		  }
		  //if thirdTok corresponding node was not found as part of the tree
		  //create a node
		  if (tn2 == null) 
        	  {
        	    Node n2 = new Node(thirdTok, "Unknown");
        	    //IO.put("Node of unknown type: "+ thirdTok);
        	    tn2 = new DefaultMutableTreeNode(n2);
        	    n2.setTreeNode(tn2);
        	  }
		  //add thirdTok node under secondTok node
		  tn1.add(tn2);
		  IO.put("TAInput.java:\tcontain " + secondTok + "\t" +thirdTok,2);
		}
		/******************************************************************************
		      CASE 3: first token in the line is other than "$INSTANCE" or "contain"
		*****************************************************************************/
		else
		{
		  //secondTok <-- name of a node in the tree
		  //thirdTok  <-- name of a node in the tree

		  DefaultMutableTreeNode root = 
					 (DefaultMutableTreeNode)treeModel.getRoot();
		  Enumeration allNodes = root.depthFirstEnumeration();
		  
		  DefaultMutableTreeNode tn1 = null;
		  DefaultMutableTreeNode tn2 = null;
		  Node n1 = null;
		  Node n2 = null;
		  
		  //search all tree for nodes with names equal to second or third token
		  while (allNodes.hasMoreElements())
		  {
		    Object i = allNodes.nextElement();
		    DefaultMutableTreeNode j = (DefaultMutableTreeNode)i;
		    Node n = (Node)j.getUserObject();
		    //node with name secondTok was found in the tree
		    if (n.getName().equals(secondTok)) 
		    {
		      tn1 = j;
		      n1 = n;
		    }
		    //node with name thirdTok was found in the tree
		    if (n.getName().equals(thirdTok))
		    {
		      tn2 = j;
		      n2 = n;
		    }
		  }
		  
		  /********************************************************************************************
		   CASES 3.1:  secondTok and thirdTok are same, but do not have a corresponding node in the tree
		   ********************************************************************************************/ 
		  if(secondTok.equals(thirdTok) && tn1==null)
		  {
		    //create only one node and add it under root
		    
		    n1 = new Node(secondTok, "Unknown");
		    //IO.put("Node of unknown type: "+ secondTok);
		    tn1 = new DefaultMutableTreeNode(n1);
		    n1.setTreeNode(tn1);
		    root.add(tn1);//add only one of the two tokens as nodes under the root
		  }
		  
		  /********************************************************************************************
		   CASES 3.2:      secondTok and thirdTok are same and have a corresponding node in the tree
		   ********************************************************************************************/ 
		  else if(secondTok.equals(thirdTok) && tn1!=null)
		  {
			// Do nothing
		  }
		 
		  
		  /********************************************************
		   CASES 3.3:    secondTok and thirdToken are not the same 
		   ********************************************************/ 
		  else 
		  {
		    /******************************************************************************
		      CASE 3.3.1:         secondTok doesn't have a corresponding node in the tree 
		    /*****************************************************************************/
		    if (tn1 == null)
		    {
			//create new node and add it under root
			
			n1 = new Node(secondTok, "Unknown");
			//IO.put("Node of unknown type: "+ secondTok);
			tn1 = new DefaultMutableTreeNode(n1);
			n1.setTreeNode(tn1);
			root.add(tn1);//add it under root
		    }
		    
		    /******************************************************************************
		      CASE 3.3.2:         thirdTok doesn't have a corresponding node in the tree 
		    /*****************************************************************************/
		    if (tn2 == null)
		    {
		    	//create new node and add it under root
			
			n2 = new Node(thirdTok, "Unknown");
			//IO.put("Node of unknown type: "+ thirdTok);
			//IO.put("firstToken := " + firstTok +" , secondToken := " +
						//secondTok + " , thirdToken := " +thirdTok);
			tn2 = new DefaultMutableTreeNode(n2);
			n2.setTreeNode(tn2);
			root.add(tn2);//add it under root
		    }
		    
		    /***********************************************************************************
		      CASE 3.3.3:     secondTok and thirdTok have corresponding nodes in the tree 
		    /***********************************************************************************/
		    //do nothing
		
		    //now create an edge from secondTok node to thirdTok node
		    
		    //NOTE: might be creating an edge from a node onto itself!!
		    
		    //edge originates in secondTok node and is directed towards thirdTok node
		    Edge e = new Edge(n1,n2,firstTok);
		    n1.addOutEdge(e);
		    n2.addInEdge(e);
		    IO.put("TAInput.java:\tEdge created from " + secondTok + " to " + thirdTok,2);
		  }
		}
		
		/************************* Read next line in input file *******************************/
		str = in.readLine();
		if (str != null) str = str.trim();
	      
	      } while ((str != null) && (!str.equals("FACT ATTRIBUTE :")));
	      
	      
	      IO.put("Reading the attributes ...",2);
	      
	      
	      // Deal with attributes here
	      if (str != null)
	      {
			str = in.readLine();
			
			if (str != null) str = str.trim();
			
			do
			{
		  		StringTokenizer attrTok = new StringTokenizer(str, " {}\t");
		  		String name = attrTok.nextToken().trim();
		  		String realName = "";
		  		//String fileName = "";
		  
		  		while (attrTok.hasMoreTokens())
		  		{
		    			String token = attrTok.nextToken();
		    			//if (token.indexOf("file=") == 0) fileName = token.substring(5);
		    			if (token.indexOf("label=") == 0) realName = token.substring(6);
		  		}
		 
		 		if (!realName.equals(""))
		  		{
		    			//change name of node here
		    			DefaultMutableTreeNode root = (DefaultMutableTreeNode)treeModel.getRoot();
		    			Enumeration allNodes = root.depthFirstEnumeration();
		    			while (allNodes.hasMoreElements())
		    			{
		      				Object i = allNodes.nextElement();
		      				DefaultMutableTreeNode j = (DefaultMutableTreeNode)i;
		      				Node n = (Node)j.getUserObject();
		      				//IO.put("@@"+n.getName()+"##"+name+"$$");
		      				
						if (n.getName().equals(name))
		      				{	
							n.setName(realName);
		      				}
		    			}	
		  		}
		  		
				str = in.readLine();
		  		
				if (str != null) str = str.trim();
			
			} while (str != null);
	      
	      }//end if
	     
	      
	      IO.put("Finished reading the input file.\n",2);
	      
	      in.close();
	    } 
	    catch(FileNotFoundException e) 
	    {
	      System.err.println(e.getMessage());
	    }
	    catch(IOException e) 
	    {
	      System.err.println(e.getMessage());
	    }
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/TAInput.java -->

### third_party/acdc/acdc/UpInducer.java

SHA-256: `89e342ff9173e37fc0ec3db1d46767d4cc6a489b4fc9ab8d0011a9f7f119c9f2` · 905 bytes

<!-- FULL_SOURCE third_party/acdc/acdc/UpInducer.java 89e342ff9173e37fc0ec3db1d46767d4cc6a489b4fc9ab8d0011a9f7f119c9f2 -->
```java
package acdc;
import javax.swing.tree.DefaultMutableTreeNode;
import java.util.*;

public class UpInducer extends Pattern
{
	public UpInducer (DefaultMutableTreeNode _root)
	{
		super(_root);
	}
	
	public void execute() 
	{
		// Remove intermediate clusters from the tree
		Vector rootChildren = nodeChildren(root);
		Iterator iv = rootChildren.iterator();
		
		while (iv.hasNext())
		{
			Node parent = (Node) iv.next();
			DefaultMutableTreeNode tparent = (DefaultMutableTreeNode) parent.getTreeNode();
			Vector subTree = allNodes(tparent);
			tparent.removeAllChildren();
			Iterator is = subTree.iterator();
			while (is.hasNext())
			{
				Node child = (Node) is.next();
				if (child.isFile())
				{
					DefaultMutableTreeNode tchild = (DefaultMutableTreeNode) child.getTreeNode();
					tchild.removeAllChildren();
					tparent.add(tchild);
				}
			}
		}
	}
}
```
<!-- END_FULL_SOURCE third_party/acdc/acdc/UpInducer.java -->
