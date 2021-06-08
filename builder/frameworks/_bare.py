#
# Default flags for bare-metal programming (without any framework layers)
#

from SCons.Script import Import

Import("env")

board_config = env.BoardConfig()

env.Append(
    CCFLAGS=[
        "-Wall",  # show warnings
        "-march=%s" % board_config.get("build.march"),
        "-mabi=%s" % board_config.get("build.mabi"),
        "-mcmodel=%s" % board_config.get("build.mcmodel")
    ],

    LINKFLAGS=[
        "-nostartfiles",
        "-static",
        "-nostdlib",
        "-march=%s" % board_config.get("build.march"),
        "-mabi=%s" % board_config.get("build.mabi"),
        "-mcmodel=%s" % board_config.get("build.mcmodel")
    ],

    LIBS=["m", "gcc"]
)

# copy CCFLAGS to ASFLAGS (-x assembler-with-cpp mode)
env.Append(ASFLAGS=env.get("CCFLAGS", [])[:])
