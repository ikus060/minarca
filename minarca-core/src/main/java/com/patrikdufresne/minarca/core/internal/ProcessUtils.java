/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.lang.management.ManagementFactory;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.SystemUtils;

import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.Kernel32Util;
import com.sun.jna.platform.win32.Psapi;
import com.sun.jna.platform.win32.Win32Exception;
import com.sun.jna.platform.win32.WinNT;
import com.sun.jna.platform.win32.WinNT.HANDLE;

/**
 * Utility class to manage processes.
 * 
 * @author Patrik Dufresne
 * 
 */
public class ProcessUtils {

    /**
     * Data structure to hold basic process information retrieved using the pid.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class ProcessInfo {
        /**
         * The pid.
         */
        public int pid;
        /**
         * The file name. e.g.: minarca.exe
         */
        public String name;
    }

    /**
     * Raised by {@link ProcessUtils} when a given pid is not found.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class NoSuchProcess extends Exception {
        public NoSuchProcess() {
        }
    }

    public static class CalledProcessError extends Exception {
        int exitCode;

        public CalledProcessError(int exitCode) {
            this.exitCode = exitCode;
        }
    }

    /**
     * Return the pid of the running process identifier.
     * 
     * @param identifier
     *            the process identifier
     * @param processName
     *            the process name to matches.
     * @return the Process or null if the process is not running.
     * 
     */
    public static ProcessInfo getPid(File pidfile, String processName) throws IOException, NoSuchProcess {
        /* Check if the process is already running */
        if (pidfile.exists()) {
            int pid;
            try {
                pid = Integer.valueOf(FileUtils.readFileToString(pidfile));
            } catch (NumberFormatException e) {
                // If the file is empty, or contains invalid data, that won't get converted to an integer. Process can't
                // be found.
                throw new NoSuchProcess();
            }
            ProcessInfo p = ProcessUtils.getPid(pid);
            if (p != null && (processName == null || p.name.equals(processName))) {
                return p;
            }
            throw new NoSuchProcess();
        }
        throw new NoSuchProcess();
    }

    /**
     * Check if the given pid exists and return the process info.
     * 
     * @param pid
     *            the process id to be verified.
     * @return return a process instance
     * @throws NoSuchProcess
     */
    public static ProcessInfo getPid(int pid) throws NoSuchProcess {
        if (SystemUtils.IS_OS_WINDOWS) {

            HANDLE p = Kernel32.INSTANCE.OpenProcess(WinNT.PROCESS_ALL_ACCESS, false, pid);
            if (p != null) {
                try {

                    final char[] filePathUnicode = new char[1025];
                    int length = Psapi.INSTANCE.GetModuleFileNameExW(p, null, filePathUnicode, filePathUnicode.length - 1);
                    if (length == 0) {
                        throw new Win32Exception(Kernel32.INSTANCE.GetLastError());
                    }

                    ProcessInfo data = new ProcessInfo();
                    data.pid = pid;
                    data.name = new File(new String(filePathUnicode)).getName();
                    return data;

                } finally {
                    Kernel32Util.closeHandle(p);
                }
            }
        }

        /* Linux */
        File cmdline = new File("/proc/" + pid + "/exe");
        if (cmdline.exists()) {
            try {
                File exe = cmdline.getCanonicalFile();
                ProcessInfo data = new ProcessInfo();
                data.pid = pid;
                data.name = exe.getName();
                return data;
            } catch (IOException e) {
                throw new IllegalStateException(e);
            }
        }
        throw new NoSuchProcess();
    }

    /**
     * Put a lock on the pid file.
     * 
     * @param identifier
     *            the application identifier.
     */
    public static void writePidFile(File pidFile) throws IOException {
        FileUtils.write(pidFile, String.valueOf(ProcessUtils.pid()));
    }

    /**
     * Return the pid of this running process.
     * 
     * @return
     */
    public static int pid() {
        // something like '<pid>@<hostname>'
        String name = ManagementFactory.getRuntimeMXBean().getName();
        int index = name.indexOf('@');
        if (index < 1) {
            throw new IllegalStateException("can't determine current running process id");
        }
        try {
            return Integer.valueOf(name.substring(0, index));
        } catch (NumberFormatException e) {
            throw new IllegalStateException("can't determine current running process id");
        }
    }

    /**
     * Send a SIGTERM signal to the given process id.
     * 
     * @param pid
     */
    public static void kill(int pid) throws NoSuchProcess {
        if (SystemUtils.IS_OS_WINDOWS) {
            try {
                java.lang.Process p = new ProcessBuilder("taskkill.exe", "/pid", Integer.toString(pid)).redirectErrorStream(true).start();
                StreamHandler sh = new StreamHandler(p);
                int returnCode = p.waitFor();
                if (returnCode != 0) {
                    throw new NoSuchProcess();
                }
                sh.getOutput();
            } catch (IOException e) {
                throw new IllegalStateException("failed to send signal to process", e);
            } catch (InterruptedException e) {
                // Nothing to do
            }
        }

    }

}
