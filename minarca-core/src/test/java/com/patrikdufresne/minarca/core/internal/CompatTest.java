package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertThat;

import org.hamcrest.Matchers;
import org.junit.Test;

public class CompatTest {

    @Test
    public void testRoots() {
        assertThat(Compat.getRootsPath().length, Matchers.greaterThan(0));
    }

}
