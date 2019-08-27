package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.util.Date;

import org.apache.commons.configuration.ConfigurationException;
import org.hamcrest.Matchers;
import org.junit.Before;
import org.junit.Test;

public class StatusTest {

    @Test
    public void testSetLastStatus() throws APIException, InterruptedException, ConfigurationException {
        Date now = new Date();

        // Check with failure
        Status.setLastStatus(LastResult.FAILURE);
        assertEquals(LastResult.FAILURE, Status.fromFile().getLastResult());
        assertThat(Status.fromFile().getLastResultDate(), Matchers.greaterThanOrEqualTo(now));

        // Check with success
        now = new Date();
        Status.setLastStatus(LastResult.SUCCESS);
        assertEquals(LastResult.SUCCESS, Status.fromFile().getLastResult());
        assertThat(Status.fromFile().getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        Date previous = Status.fromFile().getLastSuccess();
        assertThat(Status.fromFile().getLastSuccess(), Matchers.greaterThanOrEqualTo(now));

        // Check with failure again
        Status.setLastStatus(LastResult.FAILURE);
        assertEquals(LastResult.FAILURE, Status.fromFile().getLastResult());
        assertThat(Status.fromFile().getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        assertEquals(Status.fromFile().getLastSuccess(), previous);

    }

}
