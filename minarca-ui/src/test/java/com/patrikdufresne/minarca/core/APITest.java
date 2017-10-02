package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.util.Date;

import org.apache.commons.configuration.ConfigurationException;
import org.hamcrest.Matchers;
import org.junit.Before;
import org.junit.Test;

public class APITest {

    API api;

    @Before
    public void clearStatusFile() {
        api = API.instance();
    }

    @Test
    public void testSetLastStatus() throws APIException, InterruptedException, ConfigurationException {
        API api = API.instance();
        Date now = new Date();

        // Check with failure
        api.setLastStatus(LastResult.FAILURE);
        assertEquals(LastResult.FAILURE, api.getLastResult());
        assertThat(api.getLastResultDate(), Matchers.greaterThanOrEqualTo(now));

        // Check with success
        now = new Date();
        api.setLastStatus(LastResult.SUCCESS);
        assertEquals(LastResult.SUCCESS, api.getLastResult());
        assertThat(api.getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        Date previous = api.getLastSuccess();
        assertThat(api.getLastSuccess(), Matchers.greaterThanOrEqualTo(now));

        // Check with failure again
        api.setLastStatus(LastResult.FAILURE);
        assertEquals(LastResult.FAILURE, api.getLastResult());
        assertThat(api.getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        assertEquals(api.getLastSuccess(), previous);

    }

}
