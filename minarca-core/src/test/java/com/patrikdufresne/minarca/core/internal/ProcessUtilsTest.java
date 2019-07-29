/**
 * Copyright(C) 2013 Patrik Dufresne Service Logiciel <info@patrikdufresne.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertNotNull;
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
    }

    @Test
    public void testGetPidWithFile() throws IOException, NoSuchProcess {
        File f = File.createTempFile("minarca-process-utils", ".pid");
        ProcessUtils.writePidFile(f);
        ProcessInfo p = ProcessUtils.getPid(f, "java");
        assertNotNull(p);
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
