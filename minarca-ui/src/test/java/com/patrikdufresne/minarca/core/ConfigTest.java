package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.util.Date;

import org.apache.commons.configuration.ConfigurationException;
import org.hamcrest.Matchers;
import org.junit.Before;
import org.junit.Test;

public class ConfigTest {

    Config config;

    @Before
    public void clearStatusFile() {
        config = new Config();
    }

    @Test
    public void testSetLastStatus() throws APIException, InterruptedException, ConfigurationException {
        Date now = new Date();

        // Check with failure
        config.setLastStatus(LastResult.FAILURE);
        assertEquals(LastResult.FAILURE, config.getLastResult());
        assertThat(config.getLastResultDate(), Matchers.greaterThanOrEqualTo(now));

        // Check with success
        now = new Date();
        config.setLastStatus(LastResult.SUCCESS);
        assertEquals(LastResult.SUCCESS, config.getLastResult());
        assertThat(config.getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        Date previous = config.getLastSuccess();
        assertThat(config.getLastSuccess(), Matchers.greaterThanOrEqualTo(now));

        // Check with failure again
        config.setLastStatus(LastResult.FAILURE);
        assertEquals(LastResult.FAILURE, config.getLastResult());
        assertThat(config.getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        assertEquals(config.getLastSuccess(), previous);

    }

}
