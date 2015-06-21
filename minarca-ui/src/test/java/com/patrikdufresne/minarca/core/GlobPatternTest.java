package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.util.List;

import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;

public class GlobPatternTest {

    @Test
    public void testDownloadsExcludes() {

        GlobPattern pattern = new GlobPattern(SystemUtils.USER_HOME + "/Downloads");
        List<GlobPattern> list = GlobPattern.getDownloadsPatterns();
        assertTrue(list.contains(pattern));

    }
}
