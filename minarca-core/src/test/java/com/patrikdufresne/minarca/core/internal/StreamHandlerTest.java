package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertEquals;

import java.io.IOException;

import org.junit.Test;

public class StreamHandlerTest {

    @Test
    public void test() throws IOException {
        Process p = new ProcessBuilder().command("echo", "coucou").redirectErrorStream(true).start();
        StreamHandler sh = new StreamHandler(p);
        assertEquals("coucou\n", sh.getOutput());
    }

}
