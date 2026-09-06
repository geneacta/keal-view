# The C compiler for this machine, in one place because two places disagreed.
#
# `tools/build.sh` knew that MinGW-w64 ships `gcc` and no `cc` at all, and
# defaulted accordingly. `tools/test.sh` wrote its own `${CC:-cc}` and did
# not, so on Windows the suite ran 979 checks and then failed with
#
#     tools/test.sh: line 42: cc: command not found
#     FAIL  the C generated for tests/units.keal says the backend slipped
#
# — accusing the code generator of a fault that belonged to the script. That
# is the worst shape a failure can take: it names something real, and names
# the wrong one. Found by the Windows session, on a machine where `cc` genuinely
# does not exist.
#
# Sourced by both. `CC` from the environment still wins everywhere.
kv_cc() {
    case $(uname -s) in
      MINGW*|MSYS*|CYGWIN*|Windows_NT) echo "${CC:-gcc}" ;;
      *) echo "${CC:-cc}" ;;
    esac
}
