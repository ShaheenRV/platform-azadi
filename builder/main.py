import sys
from platform import system
from os import makedirs
from os.path import isdir, join

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)


env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()

env.Replace(
    AR="riscv32-unknown-elf-gcc-ar",
    AS="riscv32-unknown-elf-as",
    CC="riscv32-unknown-elf-gcc",
    GDB="riscv32-unknown-elf-gdb",
    CXX="riscv32-unknown-elf-g++",
    OBJCOPY="riscv32-unknown-elf-objcopy",
    ELFTOHEX="riscv32-unknown-elf-elf2hex",
    RANLIB="riscv32-unknown-elf-gcc-ranlib",
    SIZETOOL="riscv32-unknown-elf-size",

    ARFLAGS=["rcs"],

    SIZEPRINTCMD='$SIZETOOL -d $SOURCES',

    PROGSUFFIX=".elf"
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$ELFTOHEX",
                "--bit-width",
                "32",
                "--input",
                "$SOURCES",
                "--output",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        ),
        ElfToBin=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "binary",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".bin"
        )
    )
)

if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py", exports="env")

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
else:
    target_elf = env.BuildProgram()
    target_hex = env.ElfToHex(join("$BUILD_DIR", "${PROGNAME}"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_hex))
target_buildprog = env.Alias("buildprog", target_hex, target_hex)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default .bin file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board_config.get("debug.tools", {})
upload_actions = []
upload_target = target_elf

if upload_protocol.startswith("jlink"):

    def _jlink_cmd_script(env, source):
        build_dir = env.subst("$BUILD_DIR")
        if not isdir(build_dir):
            makedirs(build_dir)
        script_path = join(build_dir, "upload.jlink")
        commands = [
            "h",
            "loadfile %s" % source,
            "r",
            "q"
        ]
        with open(script_path, "w") as fp:
            fp.write("\n".join(commands))
        return script_path

    env.Replace(
        __jlink_cmd_script=_jlink_cmd_script,
        UPLOADER="JLink.exe" if system() == "Windows" else "JLinkExe",
        UPLOADERFLAGS=[
            "-device", env.BoardConfig().get("debug", {}).get("jlink_device"),
            "-speed", "1000",
            "-if", "JTAG",
            "-jtagconf", "-1,-1",
            "-autoconnect", "1",
            "-NoGui", "1"
        ],
        UPLOADCMD='$UPLOADER $UPLOADERFLAGS -CommanderScript "${__jlink_cmd_script(__env__, SOURCE)}"'
    )
    upload_target = target_hex
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

elif upload_protocol in debug_tools:
    # openocd_args = [
    #     "-c",
    #     "debug_level %d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1),
    #     "-s", platform.get_package_dir("tool-openocd-riscv") or ""
    # ]
    # openocd_args.extend(
    #     debug_tools.get(upload_protocol).get("server").get("arguments", []))
    # openocd_args.extend([
    #     "-c", "init; load_image {$SOURCE} %s;resume 0x80000000;shutdown" %
    #     board_config.get("upload").get("flash_start", "")
    # ])

    upload_tool = join(platform.get_package_dir(
        "framework-azadi-sdk") or "", "bsp", "util", "uploader.py")

    env.Replace(
        UPLOADER=upload_tool,
        UPLOADCMD='"$PYTHONEXE" "$UPLOADER" $SOURCE')
    upload_target = target_hex
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

AlwaysBuild(env.Alias("upload", upload_target, upload_actions))


#

Default([target_buildprog, target_size])
