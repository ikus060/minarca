package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map.Entry;

import org.apache.commons.lang.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.MinarcaMissingException;

/**
 * Utility class to locate minarca executable and launch it.
 * 
 * @author Patrik Dufresne
 * 
 */
public class MinarcaExecutable {

    private static final boolean DEV = Boolean.getBoolean("com.patrikdufresne.minarca.development");

    /**
     * The logger.
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(MinarcaExecutable.class);

    /**
     * Executable launch to start backup.
     */
    public static final String MINARCA_EXE;

    /**
     * Property used to define the location of minarca.bat file.
     */
    private static final String PROPERTY_MINARCA_LOCATION = "minarca.exe.location";

    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            if (SystemUtils.JAVA_VM_NAME.contains("64-Bit")) {
                MINARCA_EXE = "minarca64.exe";
            } else {
                MINARCA_EXE = "minarca.exe";
            }
        } else {
            MINARCA_EXE = "minarca";
        }
    }

    /**
     * Return the command line to be executed to run a backup.
     * 
     * @return
     * @throws APIException
     */
    private static String[] createMinarcaCommand(boolean development, String... extraArgs) throws MinarcaMissingException {
        // Build the command line to be executed.
        List<String> args = new ArrayList<String>();
        if (development) {
            // When running in development environment, we need to call minarca as a java process.
            File javaExe = new File(new File(System.getProperty("java.home"), "bin"), "java");
            args.add(javaExe.toString()); // usr/lib/jvm/java-8-openjdk-amd64/bin/java
            // Copy all minarca system properties.
            for (Entry<Object, Object> e : System.getProperties().entrySet()) {
                if (e.getKey().toString().startsWith("com.patrikdufresne.minarca")) {
                    args.add("-D" + e.getKey() + "=" + e.getValue());
                }
            }
            args.add("-classpath");
            args.add(System.getProperty("java.class.path"));
            args.add(System.getProperty("sun.java.command", "com.patrikdufresne.minarca.Main"));
        } else {
            // When running in production mode, execute the minarca binary directly.
            File minarcaExe = getMinarcaLocation();
            if (minarcaExe == null) {
                throw new MinarcaMissingException();
            }
            args.add(minarcaExe.toString());
        }

        args.addAll(Arrays.asList(extraArgs));
        return args.toArray(new String[0]);
    }

    /**
     * Return the location of minarca executable.
     * 
     * @return
     */
    public static File getMinarcaLocation() {
        // On Windows, user.dir will be defined as C:\Users\vmtest\AppData\Local\minarca, lookup to "./bin/" should find
        // minarca.
        return Compat.searchFile(MINARCA_EXE, System.getProperty(PROPERTY_MINARCA_LOCATION), "./bin/", ".", "/opt/minarca/bin/");
    }

    public MinarcaExecutable() {
        // Nothing to do.
    }

    /**
     * Used to start minarca executable to stop current instance.
     * 
     * @throws APIException
     */
    public void backup(boolean force) throws APIException {
        String command[];
        if (force) {
            command = createMinarcaCommand(DEV, "--backup", "--force");
        } else {
            command = createMinarcaCommand(DEV, "--backup");
        }
        execute(command);
    }

    /**
     * Execute minarca proess. Don't wait for it.
     * 
     * @param command
     * @throws APIException
     */
    private void execute(String[] command) throws APIException {
        LOGGER.debug("executing command: {}", StringUtils.join(command, " "));
        try {
            new ProcessBuilder(command).inheritIO().start();
        } catch (IOException e) {
            throw new APIException(e);
        }
    }

    /**
     * Used to start minarca executable to stop current instance.
     * 
     * @throws APIException
     */
    public void stop() throws APIException {
        // Need to stop the process.
        execute(createMinarcaCommand(DEV, "--backup", "--stop"));
    }

}
