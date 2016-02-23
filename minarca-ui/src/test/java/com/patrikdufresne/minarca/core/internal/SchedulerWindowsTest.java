package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.*;

import java.io.File;
import java.sql.Date;
import java.util.Locale;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mockito;
import org.powermock.api.mockito.PowerMockito;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;
import org.powermock.reflect.Whitebox;

import com.patrikdufresne.minarca.core.internal.SchedulerTask.LastResult;
import com.patrikdufresne.minarca.core.internal.SchedulerTask.Schedule;

@RunWith(PowerMockRunner.class)
@PrepareForTest({ SchedulerWindows.class, SystemUtils.class })
public class SchedulerWindowsTest {

    @Test
    public synchronized void testExists_ForWinXPFr() throws Exception {
        // Enforce WinXP
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) true);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) false);
        // Enforce French Local
        Locale.setDefault(Locale.CANADA_FRENCH);

        String winxpdata = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("winxp.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(winxpdata).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Program Files\\minarca\\bin\\minarca.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertTrue(info.isRunning());
        assertEquals(LastResult.FAILURE, info.getLastResult());
        assertEquals(Schedule.HOURLY, info.getSchedule());
        assertEquals(new Date(1433286360000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin7() throws Exception {
        // Enforce Win7
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);
        // Enforce French Local
        Locale.setDefault(Locale.ENGLISH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Program Files\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.FAILURE, info.getLastResult());
        assertEquals(Schedule.HOURLY, info.getSchedule());
        assertEquals(new Date(1420595256000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin7Fr_Hourly() throws Exception {
        // Enforce Win7
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);
        // Enforce French Local
        Locale.setDefault(Locale.CANADA_FRENCH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7-fr-hourly.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\vmuser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.HOURLY, info.getSchedule());
        assertEquals(new Date(1441916280000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin7Fr_Weekly() throws Exception {
        // Enforce Win7
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);
        // Enforce French Local
        Locale.setDefault(Locale.CANADA_FRENCH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7-fr-weekly.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\vmuser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.WEEKLY, info.getSchedule());
        assertEquals(new Date(1442603940000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin7Fr_Monthly() throws Exception {
        // Enforce Win7
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);
        // Enforce French Local
        Locale.setDefault(Locale.CANADA_FRENCH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7-fr-monthly.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\vmuser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.MONTHLY, info.getSchedule());
        assertEquals(new Date(1442603940000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin7Fr_Daily() throws Exception {
        // Enforce Win7
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);
        // Enforce French Local
        Locale.setDefault(Locale.CANADA_FRENCH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7-fr-daily.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\vmuser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.DAILY, info.getSchedule());
        assertEquals(new Date(1442603940000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin7Fr_Daily_Running() throws Exception {
        // Enforce Win7
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) true);
        // Enforce French Local
        Locale.setDefault(Locale.CANADA_FRENCH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win7-fr-daily-running.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\vmuser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertTrue(info.isRunning());
        assertEquals(LastResult.UNKNOWN, info.getLastResult());
        assertEquals(Schedule.DAILY, info.getSchedule());
        assertEquals(new Date(1447947060000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin10En_Hourly() throws Exception {
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) false);
        // Enforce French Local
        Locale.setDefault(Locale.ENGLISH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win10-en-hourly.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\IEUser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.HAS_NOT_RUN, info.getLastResult());
        assertEquals(Schedule.HOURLY, info.getSchedule());
        assertEquals(null, info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin10En_Daily() throws Exception {
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) false);
        // Enforce French Local
        Locale.setDefault(Locale.ENGLISH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win10-en-daily.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\IEUser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.DAILY, info.getSchedule());
        assertEquals(new Date(1442592300000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin10En_Weekly() throws Exception {
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) false);
        // Enforce French Local
        Locale.setDefault(Locale.ENGLISH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win10-en-weekly.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\IEUser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.WEEKLY, info.getSchedule());
        assertEquals(new Date(1442592300000l), info.getLastRun());
    }

    @Test
    public synchronized void testExists_ForWin10En_Monthly() throws Exception {
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_XP", (Boolean) false);
        Whitebox.setInternalState(SystemUtils.class, "IS_OS_WINDOWS_7", (Boolean) false);
        // Enforce French Local
        Locale.setDefault(Locale.ENGLISH);

        String win7data = IOUtils.toString(SchedulerWindowsTest.class.getResourceAsStream("win10-en-monthly.data"));

        SchedulerWindows s = PowerMockito.spy(new SchedulerWindows());
        PowerMockito.doReturn(win7data).when(s).execute(Mockito.anyList());
        PowerMockito.doReturn(new File("C:\\Users\\IEUser\\AppData\\Local\\minarca\\bin\\minarca64.exe")).when(s).getExeLocation();

        assertTrue(s.exists());

        SchedulerTask info = s.info();
        assertFalse(info.isRunning());
        assertEquals(LastResult.SUCCESS, info.getLastResult());
        assertEquals(Schedule.MONTHLY, info.getSchedule());
        assertEquals(new Date(1442592300000l), info.getLastRun());
    }

}
