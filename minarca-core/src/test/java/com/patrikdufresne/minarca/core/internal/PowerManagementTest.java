/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
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
