@echo off

rem -------------------------------------------------------------------------
rem
rem 使用说明：
rem
rem 1: 该脚本用于别的项目时只需要修改 MAIN_CLASS 即可运行
rem
rem 2: JAVA_OPTS 可通过 -D 传入 undertow.port 与 undertow.host 这类参数覆盖
rem    配置文件中的相同值此外还有 undertow.resourcePath, undertow.ioThreads
rem    undertow.workerThreads 共五个参数可通过 -D 进行传入
rem
rem 3: JAVA_OPTS 可传入标准的 java 命令行参数,例如 -Xms256m -Xmx1024m 这类常用参数
rem
rem
rem -------------------------------------------------------------------------

setlocal enabledelayedexpansion

:: 设置 JDK 路径
set JDK_PATH=D:\DevTools\java\jdk-18.0.2.1

:: 检查 JDK 路径是否存在
if exist %JDK_PATH% (
    :: 设置环境变量
    set JAVA_HOME=%JDK_PATH%
    set "PATH=!JAVA_HOME!\bin;!PATH!"
    set CLASS_PATH=.;!JAVA_HOME!\lib\tools.jar;!JAVA_HOME!\lib\dt.jar
    echo JDK 路径存在，已设置环境变量。
)

setlocal & pushd


rem 启动入口类,该脚本文件用于别的项目时要改这里
set MAIN_CLASS=com.jxboot.services.JxBootServicesOneX2Application

set PORT=9901
if "%2" neq "" set PORT=%2
set IP=0.0.0.0
if "%3" neq "" set IP=%3

rem Java 命令行参数,根据需要开启下面的配置,改成自己需要的,注意等号前后不能有空格
rem set "JAVA_OPTS=-Xms256m -Xmx1024m -Dundertow.port=80 -Dundertow.host=0.0.0.0"
rem set "JAVA_OPTS=-Dundertow.port=80 -Dundertow.host=0.0.0.0"
rem set "JAVA_OPTS=-Xms256m -Xmx1024m -Dundertow.port=%PORT% -Dundertow.host=%IP%"
set "JAVA_OPTS=-Xms256m -Xmx1024m%"

if "%1"=="start" goto normal
if "%1"=="stop" goto normal
if "%1"=="restart" goto normal

goto error


:error
echo Usage: jfinal.bat start | stop | restart
goto :eof


:normal
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
goto :eof


:start
set APP_BASE_PATH=%~dp0
set CP=%APP_BASE_PATH%config;%APP_BASE_PATH%lib\*
echo starting jfinal undertow
start java -Xverify:none %JAVA_OPTS% -cp %CP% %MAIN_CLASS%
goto :eof


:stop
set "PATH=%JAVA_HOME%\bin;%PATH%"
echo stopping jfinal undertow
for /f "tokens=1" %%i in ('jps -lv ^| find "-Dundertow.port=%PORT%"') do ( taskkill /F /PID %%i )
goto :eof


:restart
call :stop
call :start
goto :eof

endlocal & popd
rem pause
exit