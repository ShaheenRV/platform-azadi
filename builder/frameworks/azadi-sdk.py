from os import listdir
from os.path import isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
board_config = env.BoardConfig()

FRAMEWORK_DIR = env.PioPlatform().get_package_dir("framework-azadi-sdk")
assert FRAMEWORK_DIR and isdir(FRAMEWORK_DIR)


env.SConscript("_bare.py", exports="env")

target = env.subst("$BOARD")

env.Append(
    ASFLAGS=[
        ("-D__ASSEMBLY__=1"),
        "-fno-common"
    ],

    CFLAGS=[
        "-static",
        "-std=gnu99"
    ],

    CCFLAGS=[
        "-fno-builtin-printf"
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "bsp", "include"),
        # join(FRAMEWORK_DIR, "bsp", "third_party", target)
    ],

    LIBPATH=[
        join(FRAMEWORK_DIR, "bsp", "core", target)
    ],

    LINKFLAGS=[
        "-static"
    ],
)

if not board_config.get("build.ldscript", ""):
    env.Append(LIBPATH=[join(FRAMEWORK_DIR, "bsp", "core")])
    env.Replace(LDSCRIPT_PATH="link.ld")
    print("Using azadi linker script")

#
# Target: Build core BSP libraries
#

libs = []

for driver in listdir(join(FRAMEWORK_DIR, "bsp", "drivers")):
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "bsp", "drivers", driver),
            join(FRAMEWORK_DIR, "bsp", "drivers", driver))
    )

libs.append(
    env.BuildLibrary(
        join("$BUILD_DIR", "bsp", "core"),
        join(FRAMEWORK_DIR, "bsp", "core")
    )
)

libs.append(
    env.BuildLibrary(
        join("$BUILD_DIR", "bsp", "libs"),
        join(FRAMEWORK_DIR, "bsp", "libs")
    )
)

# libs.append(
#     env.BuildLibrary(
#         join("$BUILD_DIR", "bsp", "third_party", target),
#         join(FRAMEWORK_DIR, "bsp", "third_party", target))
# )

env.Prepend(LIBS=libs)