package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;

import org.junit.Test;
import org.mockito.Mockito;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.ScheduleNotFoundException;
import com.patrikdufresne.minarca.core.internal.Crontab.CrontabEntry;

public class SchedulerLinuxTest {

    @Test
    public void testExists() throws ScheduleNotFoundException, APIException, IOException {
        // Mock crontab
        SchedulerLinux sh = Mockito.spy(new SchedulerLinux());
        Mockito.doReturn(new CrontabEntry("@daily minarca --backup")).when(sh).find();
        // Get value
        assertTrue(sh.exists());
    }

    @Test
    public void testFind() throws ScheduleNotFoundException, APIException, IOException {
        SchedulerLinux sh = Mockito.spy(new SchedulerLinux());
        Mockito.when(sh.getExeLocation()).thenReturn(new File("minarca"));
        Crontab crontab = new Crontab(Arrays.asList(new CrontabEntry("@daily minarca --backup")));
        Mockito.when(sh.getCrontab()).thenReturn(crontab);

        // Get value
        assertTrue(sh.exists());
    }

}
