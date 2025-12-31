# First Steps

## Requirements

* Java 21 / OpenJDK 21
* Maven
* Internet connected

Install the requirements on your development host, using your preferred package managers.

## Setting it up

Open up a new terminal session, and change your working directory to the `java` subdirectory:

```
$ cd ..../modules/common/jasperreports_viaduct/java
$ mvn clean package cargo:run
```

If this is the first time you are running this, **Maven** will download all the dependencies for the webapp
from the 'Net. This may take some time. Eventually, the system will compile and start up:

```
...
[INFO] [talledLocalContainer] Jun 15, 2022 11:55:40 AM org.apache.catalina.startup.HostConfig deployDirectory
[INFO] [talledLocalContainer] INFO: Deployment of web application directory [.../odoo18/modules/common/jasperreports_viaduct/java/target/cargo/configurations/tomcat9x/webapps/host-manager] has finished in [64] ms
[INFO] [talledLocalContainer] Jun 15, 2022 11:55:40 AM org.apache.coyote.AbstractProtocol start
[INFO] [talledLocalContainer] INFO: Starting ProtocolHandler ["http-nio-8080"]
[INFO] [talledLocalContainer] Jun 15, 2022 11:55:40 AM org.apache.catalina.startup.Catalina start
[INFO] [talledLocalContainer] INFO: Server startup in [3,009] milliseconds
[INFO] [talledLocalContainer] Tomcat 9.x started on port [8080]
[INFO] Press Ctrl-C to stop the container...

```

Congratulations! The webapp is active on your development host. Keep the application active as you work on the report.

## Common Errors

### Missing Project Exception

```
[INFO] Scanning for projects...
[INFO] ------------------------------------------------------------------------
[INFO] BUILD FAILURE
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  0.050 s
[INFO] Finished at: 2022-06-15T11:59:27+12:00
[INFO] ------------------------------------------------------------------------
[ERROR] The goal you specified requires a project to execute but there is no POM in this directory (.../odoo18/modules/common/jasperreports_viaduct). Please verify you invoked Maven from the correct directory. -> [Help 1]
[ERROR] 
[ERROR] To see the full stack trace of the errors, re-run Maven with the -e switch.
[ERROR] Re-run Maven using the -X switch to enable full debug logging.
[ERROR] 
[ERROR] For more information about the errors and possible solutions, please read the following articles:
[ERROR] [Help 1] http://cwiki.apache.org/confluence/display/MAVEN/MissingProjectException
```

You are in the wrong working directory. The current directory must have a `pom.xml` present.

### Port number in use

```
[INFO] [stalledLocalDeployer] Deploying [.../odoo18/modules/common/jasperreports_viaduct/java/target/jasperreports-viaduct18.war] to [/home/jonc/work/erp/odoo18/modules/common/jasperreports_viaduct/java/target/cargo/configurations/tomcat9x/webapps]...
[WARNING] [talledLocalContainer] org.codehaus.cargo.container.ContainerException: Port number 8205 (defined with the property cargo.rmi.port) is in use. Please free it on the system or set it to a different port in the container configuration.
[ERROR] Starting container [org.codehaus.cargo.container.tomcat.Tomcat9xInstalledLocalContainer@72a7aa4f] failed
org.codehaus.cargo.container.ContainerException: Port number 8205 (defined with the property cargo.rmi.port) is in use. Please free it on the system or set it to a different port in the container configuration.
    at org.codehaus.cargo.container.spi.AbstractLocalContainer.start (AbstractLocalContainer.java:214)
    at org.codehaus.cargo.maven2.ContainerStartMojo.executeLocalContainerAction (ContainerStartMojo.java:84)
    at org.codehaus.cargo.maven2.ContainerRunMojo.doExecute (ContainerRunMojo.java:96)
    at org.codehaus.cargo.maven2.AbstractCargoMojo.execute (AbstractCargoMojo.java:471)
    at org.apache.maven.plugin.DefaultBuildPluginManager.executeMojo (DefaultBuildPluginManager.java:137)
    at org.apache.maven.lifecycle.internal.MojoExecutor.doExecute (MojoExecutor.java:301)
    at org.apache.maven.lifecycle.internal.MojoExecutor.execute (MojoExecutor.java:211)
    at org.apache.maven.lifecycle.internal.MojoExecutor.execute (MojoExecutor.java:165)
    at org.apache.maven.lifecycle.internal.MojoExecutor.execute (MojoExecutor.java:157)
    at org.apache.maven.lifecycle.internal.LifecycleModuleBuilder.buildProject (LifecycleModuleBuilder.java:121)
    at org.apache.maven.lifecycle.internal.LifecycleModuleBuilder.buildProject (LifecycleModuleBuilder.java:81)
    at org.apache.maven.lifecycle.internal.builder.singlethreaded.SingleThreadedBuilder.build (SingleThreadedBuilder.java:56)
    at org.apache.maven.lifecycle.internal.LifecycleStarter.execute (LifecycleStarter.java:127)
    at org.apache.maven.DefaultMaven.doExecute (DefaultMaven.java:294)
    at org.apache.maven.DefaultMaven.doExecute (DefaultMaven.java:192)
    at org.apache.maven.DefaultMaven.execute (DefaultMaven.java:105)
    at org.apache.maven.cli.MavenCli.execute (MavenCli.java:960)
    at org.apache.maven.cli.MavenCli.doMain (MavenCli.java:293)
    at org.apache.maven.cli.MavenCli.main (MavenCli.java:196)
    at jdk.internal.reflect.NativeMethodAccessorImpl.invoke0 (Native Method)
    at jdk.internal.reflect.NativeMethodAccessorImpl.invoke (NativeMethodAccessorImpl.java:62)
    at jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke (DelegatingMethodAccessorImpl.java:43)
    at java.lang.reflect.Method.invoke (Method.java:566)
    at org.codehaus.plexus.classworlds.launcher.Launcher.launchEnhanced (Launcher.java:282)
    at org.codehaus.plexus.classworlds.launcher.Launcher.launch (Launcher.java:225)
    at org.codehaus.plexus.classworlds.launcher.Launcher.mainWithExitCode (Launcher.java:406)
    at org.codehaus.plexus.classworlds.launcher.Launcher.main (Launcher.java:347)
    at org.codehaus.classworlds.Launcher.main (Launcher.java:47)
[INFO] Press Ctrl-C to stop the container...
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  3.310 s
[INFO] Finished at: 2022-06-15T12:01:01+12:00
[INFO] ------------------------------------------------------------------------
```

You already have an instance of **jasperreports_viaduct** running. Look for it and stop the other instance if required.
