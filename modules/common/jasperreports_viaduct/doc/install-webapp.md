# Installation

These are the instructions to install the **jasperreports_viaduct18.war** web app on a Production System.
It is not required for Development Systems; as a simpler, transient method is available.

## Requirements

* Java 21
* [Apache Tomcat](https://tomcat.apache.org) version 9 or later

## Deployment

Compile the webapp in the `java` subdirectory and deploy the **jasperreports_viaduct18.war** application.
Java 21 should be used to compile the webapp. The Tomcat instance should also be using Java 21.

```
$ cd java
$ mvn clean package
$ cp target/jasperreports_viaduct18.war /path/to/tomcat/webapps
```

On Linux systems, the default Tomcat webapps directory is `/var/lib/tomcat/webapps`.

Only **one** active webapp is required on a host, even if there are multiple Odoo instances active on its installed
host. The webapp will render report-requests from all attaching Odoo instances.

## Viaduct Configuration

Create a log directory for the webapp, writable by the **tomcat** instance. In this document, this will be
`/var/log/viaduct`.

As root:

```
# mkdir /var/log/viaduct
# chown tomcat /var/log/viaduct
```

The webapp needs to know where it can log messages. Create the configuration file
`/usr/local/etc/viaduct-log4j2.properties` with the following content:

```
#
#       Log4j2 Configuration
#       - referenced by ${log4jConfiguration} context-param
#
property.filename = /var/log/viaduct/viaduct.log
property.pattern = %d{ISO8601} %p [%c{1}] - %m%n

appender.console.type = Console
appender.console.name = STDOUT
appender.console.layout.type = PatternLayout
appender.console.layout.pattern = ${pattern}
appender.console.layout.charset = UTF-8

appender.rolling.type = RollingFile
appender.rolling.name = RollingFile
appender.rolling.fileName = ${filename}
appender.rolling.filePattern = ${filename}.%d{yyyy-MM}
appender.rolling.layout.type = PatternLayout
appender.rolling.layout.pattern = ${pattern}
appender.rolling.layout.charset = UTF-8
appender.rolling.policies.type = Policies
appender.rolling.policies.time.type = TimeBasedTriggeringPolicy
appender.rolling.policies.time.modulate = true

logger.rolling.name = nz.optimysme
logger.rolling.level = debug
logger.rolling.additivity = false
logger.rolling.appenderRef.rolling.ref = RollingFile
logger.rolling.appenderRef.stdout.ref = STDOUT

rootLogger.level = info
rootLogger.appenderRef.rolling.ref = RollingFile
rootLogger.appenderRef.stdout.ref = STDOUT
```

A template copy of this can be found in `java/src/main/properties/log4j2.properties`. Change **property.filename** as
required.

Create the webapp context file with the following content:

```
<!--
    For Tomcat deployment, this file should be copied to:
      ${catalina.base}/conf/Catalina/localhost/${warName}.xml
  -->
<Context>
  <Parameter name="log4jConfiguration"
    value="file:///usr/local/etc/viaduct-log4j2.properties"/>
</Context>
```

A template copy of this can be found in `java/src/main/properties/viaduct-context.xml.sample`.

On Linux systems, the default **catalina.base** is `/etc/tomcat9`. The context file to be created would then be
`/etc/tomcat9/conf/Catalina/localhost/jasperreports-viaduct18.xml`.

Restart the **tomcat** service once these changes have been completed.
