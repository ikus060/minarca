/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.io.File;
import java.io.IOException;

import org.apache.commons.io.FileUtils;
import org.junit.Test;

import com.patrikdufresne.minarca.core.internal.ProcessUtils.NoSuchProcess;
import com.patrikdufresne.minarca.core.internal.ProcessUtils.ProcessInfo;

public class ProcessUtilsTest {

    @Test
    public void testPid() {
        ProcessUtils.pid();
    }

    @Test
    public void testGetPid() throws NoSuchProcess {
        int pid = ProcessUtils.pid();
        ProcessInfo p = ProcessUtils.getPid(pid);
        assertNotNull(p);
        assertTrue("process name should be java:" + p.name, p.name.startsWith("java"));
    }

    @Test
    public void testGetPidWithFile() throws IOException, NoSuchProcess {
        // Get current pid
        ProcessInfo p = ProcessUtils.getPid(ProcessUtils.pid());

        File f = File.createTempFile("minarca-process-utils", ".pid");
        ProcessUtils.writePidFile(f);
        ProcessInfo p2 = ProcessUtils.getPid(f, p.name);
        assertNotNull(p2);
        assertEquals(p.name, p2.name);
    }

    @Test
    public void testGetPidWithFileNotExists() throws IOException {
        File f = File.createTempFile("minarca-process-utils", ".pid");
        try {
            ProcessUtils.getPid(f, "java");
            fail("should raise exception");
        } catch (NoSuchProcess e) {
            // Pass
        }
    }

    @Test
    public void testGetPidWithFilePidNotExists() throws IOException {
        File f = File.createTempFile("minarca-process-utils", ".pid");
        FileUtils.write(f, "2345678");
        try {
            ProcessUtils.getPid(f, "java");
            fail("should raise exception");
        } catch (NoSuchProcess e) {
            // Pass
        }
    }

}
