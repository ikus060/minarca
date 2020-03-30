FROM buildpack-deps:buster

ENV DEBIAN_FRONTEND noninteractive

# wine settings
ENV WINEPREFIX /wine-prefix/
ENV WINEARCH   win32
ENV WINEDEBUG  fixme-all

RUN set -x \
    && dpkg --add-architecture i386 && apt-get update && apt-get install -y --no-install-recommends wine wine32 xvfb xauth cabextract winbind fonts-wine ca-certificates \
    && apt-get clean \
    && wget -nv -O /usr/local/bin/winetricks 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks' \
    && chmod +x /usr/local/bin/winetricks \
    && wineboot -u

# jre-8u231-windows-x64.exe
ARG JDK_URL=https://github.com/frekele/oracle-java/releases/download/8u212-b10/jdk-8u212-windows-i586.exe
ARG MVN_URL=http://apache.mirror.vexxhost.com/maven/maven-3/3.6.3/binaries/apache-maven-3.6.3-bin.tar.gz

# Install java
# https://docs.oracle.com/javase/8/docs/technotes/guides/install/config.html#installing_with_config_file
RUN set -x \
    && wineboot -u \
    && winetricks win7 \
    && wget -nv -O "jdk_setup.exe" "$JDK_URL" \
    && (Xvfb :99 &) && export DISPLAY=:99 \
    && wine "jdk_setup.exe" /s REBOOT=Disable AUTO_UPDATE=0 WEB_JAVA=0 WEB_ANALYTICS=0 INSTALLDIR=C:\\java\\jdk /L "jdk_setup.log" \
    && rm jdk_setup.exe \
    && wine "C:\java\jdk\bin\java.exe" -version \
    && echo 'wine C:\\\\java\\\\jdk\\\\bin\\\\java.exe "$@"' > /usr/bin/java \
    && echo 'wine C:\\\\java\\\\jdk\\\\bin\\\\javac.exe "$@"' > /usr/bin/javac \
    && echo 'wine C:\\\\java\\\\jdk\\\\bin\\\\javaw.exe "$@"' > /usr/bin/javaw \
    && chmod +x /usr/bin/java \
    && chmod +x /usr/bin/javac \
    && chmod +x /usr/bin/javaw \
    && /usr/bin/java -version

ENV JAVA_HOME="C:\java\jdk"
ENV WINEPATH="C:\maven\bin;C:\java\jdk\bin;C:\windows\system32;C:\windows;C:\windows\system32\wbem"

# Install maven
ADD mvn.cmd.patch /mvn.cmd.patch
RUN set -x \
    && apt-get update && apt-get install -y --no-install-recommends dos2unix && apt-get clean \
    && wget -nv -O apache-maven.tar.gz "$MVN_URL" \
    && mkdir "$WINEPREFIX/drive_c/maven" \
    && tar -C "$WINEPREFIX/drive_c/maven" -zxvf apache-maven.tar.gz --strip 1 \
    && rm apache-maven.tar.gz \
    && dos2unix "$WINEPREFIX/drive_c/maven/bin/mvn.cmd" \
    && patch -l "$WINEPREFIX/drive_c/maven/bin/mvn.cmd" /mvn.cmd.patch \
    && unix2dos "$WINEPREFIX/drive_c/maven/bin/mvn.cmd" \
    && rm /mvn.cmd.patch \
    && echo 'wine cmd /c C:\\\\maven\\\\bin\\\\mvn.cmd "$@"' > /usr/bin/mvn \
    && chmod +x /usr/bin/mvn \
    && /usr/bin/mvn -version 
