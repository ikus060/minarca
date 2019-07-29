package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;

import org.apache.commons.io.FileUtils;
import org.junit.Test;

import com.patrikdufresne.minarca.core.internal.Crontab;
import com.patrikdufresne.minarca.core.internal.Crontab.CrontabEntry;

public class CrontabTest {

    /**
     * Parse a full crontab.
     * 
     * @throws URISyntaxException
     * @throws IOException
     */
    @Test
    public void testParse() throws URISyntaxException, IOException {
        File file = new File(CrontabTest.class.getResource("crontab1.data").toURI());
        String data = FileUtils.readFileToString(file);
        Crontab crontab = Crontab.parse(data);
        assertEquals(4, crontab.getEntries().size());
        // Check each entry
        // 0 2 12 * * /usr/bin/find
        CrontabEntry entry1 = crontab.getEntries().get(0);
        assertEquals("0", entry1.getMinute());
        assertEquals("2", entry1.getHour());
        assertEquals("12", entry1.getDayOfMonth());
        assertEquals("*", entry1.getMonth());
        assertEquals("*", entry1.getDayOfWeek());
        assertEquals("0 2 12 * *", entry1.getInterval());
        assertEquals("/usr/bin/find", entry1.getCommand());

        // * * * * * /sbin/ping -c 1 192.168.0.1 > /dev/null
        CrontabEntry entry2 = crontab.getEntries().get(1);
        assertEquals("*", entry2.getMinute());
        assertEquals("*", entry2.getHour());
        assertEquals("*", entry2.getDayOfMonth());
        assertEquals("*", entry2.getMonth());
        assertEquals("*", entry2.getDayOfWeek());
        assertEquals("/sbin/ping -c 1 192.168.0.1 > /dev/null", entry2.getCommand());

        // 0 0,12 1 */2 * /sbin/ping -c 192.168.0.1; ls -la >>/var/log/cronrun
        CrontabEntry entry3 = crontab.getEntries().get(2);
        assertEquals("0", entry3.getMinute());
        assertEquals("0,12", entry3.getHour());
        assertEquals("1", entry3.getDayOfMonth());
        assertEquals("*/2", entry3.getMonth());
        assertEquals("*", entry3.getDayOfWeek());
        assertEquals("/sbin/ping -c 192.168.0.1; ls -la >>/var/log/cronrun", entry3.getCommand());

        // * * * * * /sbin/ping -c 1 192.168.0.1 > /dev/null
        CrontabEntry entry4 = crontab.getEntries().get(3);
        assertEquals("@hourly", entry4.getInterval());
        assertEquals("/path/to/command", entry4.getCommand());

    }

    /**
     * Parse a crontab.
     * 
     * @throws URISyntaxException
     * @throws IOException
     */
    @Test
    public void testParse2() throws URISyntaxException, IOException {
        File file = new File(CrontabTest.class.getResource("crontab2.data").toURI());
        String data = FileUtils.readFileToString(file);
        Crontab crontab = Crontab.parse(data);
        assertEquals(2, crontab.getEntries().size());
        // Check line.
        CrontabEntry entry1 = crontab.getEntries().get(1);
        assertEquals("58", entry1.getMinute());
        assertEquals("17", entry1.getHour());
        assertEquals("*", entry1.getDayOfMonth());
        assertEquals("*", entry1.getMonth());
        assertEquals("*", entry1.getDayOfWeek());
        assertEquals("/opt/minarca/bin/minarca --backup", entry1.getCommand());
    }

    /**
     * Parse a crontab line.
     */
    @Test
    public void testParseLine_WithCommand() {
        CrontabEntry entry = new CrontabEntry("*/45 * * * * ?");
        assertEquals("*/45", entry.getMinute());
        assertEquals("*", entry.getHour());
        assertEquals("*", entry.getDayOfMonth());
        assertEquals("*", entry.getMonth());
        assertEquals("*", entry.getDayOfWeek());
        assertEquals("?", entry.getCommand());
        assertNull(entry.getComment());
    }

    /**
     * Parse a crontab line.
     */
    @Test
    public void testParseLine_WithComment() {
        CrontabEntry entry = new CrontabEntry("# This some comment.");
        assertNull(entry.getMinute());
        assertNull(entry.getHour());
        assertNull(entry.getDayOfMonth());
        assertNull(entry.getMonth());
        assertNull(entry.getDayOfWeek());
        assertNull(entry.getCommand());
        assertEquals("# This some comment.", entry.getComment());
    }

}
