@echo off
set JAVA_HOME=D:\DevTools\java\jdk-17.0.9
set CLASS_PATH=%JAVA_HOME%\lib\dt.jar;%JAVA_HOME%\lib\tools.jar;.;
mvn package