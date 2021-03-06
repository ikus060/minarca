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

import static org.junit.Assert.*;

import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;

public class PowerManagementTest {

    @Test
    public void testInhibit() {
        if (SystemUtils.IS_OS_LINUX && !"gnome-xorg".equals(System.getenv("DESKTOP_SESSION"))) {
            // Skip the test. Nothing to inhibit if gnome session is not used.
            return;
        }
        assertFalse("Should not be inhibited when starting test", PowerManagement.isInhibited());
        PowerManagement.inhibit();
        assertTrue("expect system to be inhibit", PowerManagement.isInhibited());
        PowerManagement.uninhibit();
        assertFalse("expect system to be uninhibit", PowerManagement.isInhibited());
    }

}
