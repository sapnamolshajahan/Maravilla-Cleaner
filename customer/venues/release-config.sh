#
# Shell variables used by various scripts on release-hosts
#
# Create a symbolic link to this file from the customer's home directory
#
RELEASE_CUSTOMER="venues" 		# customer/${directory}
RELEASE_USER="${RELEASE_CUSTOMER}"	# release files owner on release-host
RELEASE_GROUP="odoo"			# release files group on release-host

RELEASE_KEEP="3"			# number of releases to keep
RELEASE_PREFIX="${RELEASE_CUSTOMER}-release-"
RELEASE_RC_PREFIX="${RELEASE_CUSTOMER}-rc-"
RELEASE_MODULES="${RELEASE_CUSTOMER}"
