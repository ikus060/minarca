/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertEquals;

import java.io.IOException;

import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;

public class StreamHandlerTest {

    @Test
    public void test() throws IOException {
        Process p;
        if (SystemUtils.IS_OS_LINUX) {
            p = new ProcessBuilder().command("echo", "coucou").redirectErrorStream(true).start();
        } else {
            p = new ProcessBuilder().command("cmd", "/c", "echo", "coucou").redirectErrorStream(true).start();
        }
        StreamHandler sh = new StreamHandler(p);
        assertEquals("coucou" + Compat.LINEENDING, sh.getOutput());
    }

}
