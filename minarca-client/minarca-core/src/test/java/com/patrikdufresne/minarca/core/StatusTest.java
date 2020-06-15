/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.util.Date;

import org.apache.commons.configuration.ConfigurationException;
import org.hamcrest.Matchers;
import org.junit.Before;
import org.junit.Test;

public class StatusTest {

    @Test
    public void setLastStatus() throws APIException, InterruptedException, ConfigurationException {
        Date now = new Date();

        // Check with failure
        Status.setLastStatus(LastResult.FAILURE, "some error message");
        assertEquals(LastResult.FAILURE, Status.fromFile().getLastResult());
        assertThat(Status.fromFile().getLastResultDate(), Matchers.greaterThanOrEqualTo(now));

        // Check with success
        now = new Date();
        Status.setLastStatus(LastResult.SUCCESS, null);
        assertEquals(LastResult.SUCCESS, Status.fromFile().getLastResult());
        assertThat(Status.fromFile().getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        Date previous = Status.fromFile().getLastSuccess();
        assertThat(Status.fromFile().getLastSuccess(), Matchers.greaterThanOrEqualTo(now));

        // Check with failure again
        Status.setLastStatus(LastResult.FAILURE, "some error message");
        assertEquals(LastResult.FAILURE, Status.fromFile().getLastResult());
        assertThat(Status.fromFile().getLastResultDate(), Matchers.greaterThanOrEqualTo(now));
        assertEquals(Status.fromFile().getLastSuccess(), previous);

    }

    @Test
    public void setLastStatusWithDetails() throws APIException, InterruptedException, ConfigurationException {
        // Empty string
        Status.setLastStatus(LastResult.FAILURE, null);
        assertEquals(null, Status.fromFile().getDetails());

        // Empty string
        Status.setLastStatus(LastResult.FAILURE, "");
        assertEquals("", Status.fromFile().getDetails());

        // With single string
        Status.setLastStatus(LastResult.FAILURE, "some error message");
        assertEquals("some error message", Status.fromFile().getDetails());

        // With single string
        Status.setLastStatus(LastResult.FAILURE, "some, error, message");
        assertEquals("some, error, message", Status.fromFile().getDetails());

    }

}
