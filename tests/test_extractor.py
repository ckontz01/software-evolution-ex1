"""Compile a tiny owned fixture and verify the real extractor's CSV evidence.

The fixture covers the course's seven relations and the normalization and
declaration-resolution cases that can silently corrupt UE.  Target fixture
classes are never executed.  A small ASM pass changes symbolic owners to legal
inherited owners, making the lookup tests independent of ECJ's constant-pool
owner choices.  The field case exercises the JVMS interface-before-superclass
rule even though Java source rejects the corresponding ambiguous field syntax.
"""

import csv
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

from evolution.omnipresent import detect_omnipresent
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
        (source / "fixture/Sample.java").write_text(SAMPLE_SOURCE)
        (source / "fixture/MissingSource.java").write_text("package fixture; public class MissingSource {}\n")
        (source / "external/Library.java").write_text(
            "package external; public class Library { public static Object convert() { return null; } }\n"
        )
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
        cls.output = cls.work / "out"
        cls.run_extractor(cls.output)
        cls.classes = cls.read_csv("classes.csv")
        cls.aliases = cls.read_csv("class_aliases.csv")
        cls.relations = cls.read_csv("dependencies_typed.csv")
        cls.members = cls.read_csv("member_dependencies.csv")
        cls.counts = {r["metric"]: int(r["value"]) for r in cls.read_csv("extraction_counts.csv")}
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
        return cls.run_command([
            cls.java, "-cp", os.pathsep.join((str(cls.extractor), str(cls.asm))),
            "DependencyExtractor", str(cls.jar), str(cls.sources_jar), str(output), "fixture",
        ])

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


if __name__ == "__main__":
    unittest.main()
