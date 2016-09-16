package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;

public class GlobPatternTest {

    @Test
    public void testDownloadsExcludes() {
        GlobPattern pattern = new GlobPattern(true, SystemUtils.USER_HOME + "/Downloads");
        assertTrue(GlobPattern.DEFAULTS.contains(pattern));
    }

    @Test
    public void testReadWrite() throws IOException {
        GlobPattern pattern = new GlobPattern(true, SystemUtils.USER_HOME + "/Downloads");
        File temp = File.createTempFile("minaca", "globpattern");
        GlobPattern.writePatterns(temp, Arrays.asList(pattern));

        List<GlobPattern> list = GlobPattern.readPatterns(temp);
        assertEquals(1, list.size());
        assertEquals(pattern, list.get(0));

    }
}
