#!/usr/bin/env bash
#set -x
#
# Start Odoo server.
#
# Arguments:
#	1. virtual environment
#	2. odoo configuration file
#	3. pidfile
#	4. optional log directory
#
showUsage ()
{
	echo "Usage: $(basename $0) [--workon WORKON_HOME] venv-name configfile pidfile [log-directory]"
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

runOdoo ()
{
	vWrapper
	workon ${VENV}
	odoo/odoo-bin -c ${CONFIG} \
		--pidfile=${PIDFILE} \
		--data-dir="${DATADIR}"
	rm -rf ${DATADIR}
}

#
# Process arguments
#
while [ $# -gt 0 ]
do
	case ${1} in
		--workon)
			shift
			export WORKON_HOME=$(realpath ${1})
			;;
		*)
			break;;
	esac
	shift
done
if [ "$#" -lt 3 ]
then
   showUsage
fi

VENV=${1}
CONFIG=${2}
PIDFILE=${3}
LOGDIR=${4}

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
BASE=$(realpath ${BASE}/..)
DATADIR="data-dirs/$$"

umask 027
cd ${BASE}
if [ -n "${LOGDIR}" ]
then
	(runOdoo) 2>&1 | cronolog ${LOGDIR}/%Y-%m-%d.log &
else
	runOdoo
fi
