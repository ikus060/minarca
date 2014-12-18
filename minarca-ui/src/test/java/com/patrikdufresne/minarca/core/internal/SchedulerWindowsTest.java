package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertTrue;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mockito;
import org.powermock.api.mockito.PowerMockito;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;
import org.powermock.reflect.Whitebox;

@RunWith(PowerMockRunner.class)
@PrepareForTest({ SchedulerWindows.class, SystemUtils.class })
public class SchedulerWindowsTest {

    @Test
    public void testExists_ForWinXP() throws Exception {
        // Enforce WinXP
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) true);

        String winxpdata = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("winxp.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(winxpdata).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn("C:\\Program Files\\minarca\\bin\\launch.vbs").when(s).search("launch.vbs");

        assertTrue(s.exists());
    }

    @Test
    public void testExists_ForWin7() throws Exception {
        // Enforce WinXP
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn("C:\\Program Files\\minarca\\bin\\launch.vbs").when(s).search("launch.vbs");

        assertTrue(s.exists());
    }

}
