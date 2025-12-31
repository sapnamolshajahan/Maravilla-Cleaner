#!/usr/bin/env bash
#set -x
#
# Wrapper script for system startup.
#
# Arguments:
#	1. virtual environment
#	3. optional log directory
#
showUsage ()
{
	echo "Usage: $(basename $0) [--workon WORKON_HOME] venv-name config [log-directory]"
	exit 1
}

vWrapper ()
{
	for D in /usr/local/bin /usr/share/virtualenvwrapper
	do
		W="${D}/virtualenvwrapper.sh"
		if [ -r ${W} ]
		then
				VWRAPPER=${W}
				break
		fi
	done
	if [ -z "${VWRAPPER}" ]
	then
		echo "ERROR: virtualenvwrapper.sh not found"
		exit 1
	fi
	source ${VWRAPPER}
}

runAgent ()
{
	workon ${VENV}
	./remote_print_agent.py ${CONFIG}
}

#
# Process arguments
#
while (($#))
do
	case ${1} in
		--workon)
			shift
			export WORKON_HOME=$(realpath ${1})
			vWrapper
			;;
		*)
			break;;
	esac
	shift
done
if [ "$#" -lt 2 ]
then
   showUsage
fi

VENV=${1}
CONFIG=${2}
LOGDIR=${3}

#
# Sanity checks
#
# virtualenvwrapper
if [ -z "${WORKON_HOME}" ]
then
   echo "ERROR: WORKON_HOME needs to be specified"
   exit 1
fi
if [ ! -d "${WORKON_HOME}/${VENV}" ]
then
   echo "ERROR: Virtual Environment ${VENV} not found"
   exit 1
fi

# logdir
if [ -n "${LOGDIR}" -a ! -d "${LOGDIR}" ]
then
	echo "ERROR: Log directory ${LOGDIR} not found"
	exit 1
fi

#
# Invocation
#
BASE=$(dirname ${0})
BASE=$(realpath ${BASE})

umask 022
cd ${BASE}
if [ -n "${LOGDIR}" ]
then
	(runAgent) 2>&1 | cronolog ${LOGDIR}/%Y-%m-%d.log
else
	runAgent
fi
