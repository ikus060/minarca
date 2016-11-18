package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mockito;
import org.powermock.api.mockito.PowerMockito;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.ScheduleNotFoundException;
import com.patrikdufresne.minarca.core.internal.Crontab.CrontabEntry;

@RunWith(PowerMockRunner.class)
@PrepareForTest({ Crontab.class, MinarcaExecutable.class })
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
        // Mock crontab
        SchedulerLinux sh = Mockito.spy(new SchedulerLinux());
        PowerMockito.spy(MinarcaExecutable.class);
        PowerMockito.when(MinarcaExecutable.getMinarcaLocation()).thenReturn(new File("minarca"));

        PowerMockito.spy(Crontab.class);
        Crontab crontab = new Crontab(Arrays.asList(new CrontabEntry("@daily minarca --backup")));
        PowerMockito.when(Crontab.readAll()).thenReturn(crontab);

        // Get value
        assertTrue(sh.exists());
    }

}
