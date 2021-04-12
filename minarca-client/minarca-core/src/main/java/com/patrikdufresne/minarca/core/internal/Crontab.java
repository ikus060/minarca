package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Utility class to read a crontab.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Crontab {

    /**
     * Instance of this class represent a crontab entry.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static class CrontabEntry {

        /**
         * The command
         */
        private String command;

        /**
         * The comments.
         */
        private String comment;

        /**
         * The day of month
         */
        private String dayOfMonth;

        /**
         * The day of month.
         */
        private String dayOfWeek;

        /**
         * The hour
         */
        private String hour;

        /**
         * The interval.
         */
        private String interval;

        /**
         * The crontab line.
         */
        private final String line;

        /**
         * The minute
         */
        private String minute;

        /**
         * The month.
         */
        private String month;

        /**
         * Create a cron tab entry.
         * 
         * @param line
         */
        public CrontabEntry(String line) {
            Validate.notNull(line);
            this.line = line.trim();
            parseLine(this.line);
        }

        /**
         * Create a new cron tab entry.
         * 
         * @param interval
         *            the interval (express with @hourly or "* * * * *")
         * 
         * @param command
         *            the command line
         */
        public CrontabEntry(String interval, String command) {
            this(StringUtils.join(Arrays.asList(interval, command), " "));
        }

        /**
         * Create a new cron tab entry.
         * 
         * @param interval
         *            the interval (express with @hourly or "* * * * *")
         * 
         * @param command
         *            the command line
         */
        public CrontabEntry(String hour, String minute, String dayOfMonth, String month, String dayOfWeek, String command) {
            this(StringUtils.join(Arrays.asList(hour, minute, dayOfMonth, month, dayOfWeek, command), " "));
        }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (obj == null) return false;
            if (getClass() != obj.getClass()) return false;
            CrontabEntry other = (CrontabEntry) obj;
            if (line == null) {
                if (other.line != null) return false;
            } else if (!line.equals(other.line)) return false;
            return true;
        }

        public String getCommand() {
            return command;
        }

        public String getComment() {
            return comment;
        }

        public String getDayOfMonth() {
            return dayOfMonth;
        }

        public String getDayOfWeek() {
            return dayOfWeek;
        }

        public String getHour() {
            return hour;
        }

        public String getInterval() {
            return interval;
        }

        public String getLine() {
            return line;
        }

        public String getMinute() {
            return minute;
        }

        public String getMonth() {
            return month;
        }

        @Override
        public int hashCode() {
            final int prime = 31;
            int result = 1;
            result = prime * result + ((line == null) ? 0 : line.hashCode());
            return result;
        }

        private void parseLine(String line) {
            // Parse a comment line.
            if (line.startsWith("#")) {
                this.comment = line;
                return;
            }
            // Parse command line starting with "@"
            if (line.startsWith("@")) {
                try {
                    String[] fields = line.split(" ", 2);
                    this.interval = fields[0];
                    this.command = fields[1];
                    return;
                } catch (ArrayIndexOutOfBoundsException e) {
                    LOGGER.trace("fail to parse cron line: {}", this.line);
                }
            }
            // Parse a command line.
            try {
                String[] fields = line.split("\\s+", 6);
                this.minute = fields[0];
                this.hour = fields[1];
                this.dayOfMonth = fields[2];
                this.month = fields[3];
                this.dayOfWeek = fields[4];
                this.command = fields[5];
                this.interval = fields[0] + " " + fields[1] + " " + fields[2] + " " + fields[3] + " " + fields[4];
            } catch (ArrayIndexOutOfBoundsException e) {
                LOGGER.trace("fail to parse cron line: {}", this.line);
            }
        }

    }

    /**
     * Logger.
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(Crontab.class);

    /**
     * Add the given entry to crontab.
     * 
     * @param entry
     * @throws IOException
     */
    public static void addEntry(CrontabEntry entry) throws IOException {
        Validate.notNull(entry);
        // Read current crontab.
        Crontab crontab = readAll();
        // Add entry to crontab
        crontab.add(entry);
        // Generate a temporary file.
        File file = File.createTempFile("minarca", "crontab");
        try {
            FileUtils.write(file, crontab.toString());
            // Install crontab
            String output = execute(Arrays.asList(file.toString()));
            if (!output.isEmpty()) {
                throw new IOException(output);
            }
        } finally {
            // Delete temporary file
            file.delete();
        }
    }

    /**
     * Execute the crontab command line.
     * 
     * @param args
     *            the arguments
     * @return the output of the command line.
     * @throws IOException
     *             if an I/O error occurs
     */
    private static String execute(List<String> args) throws IOException {
        List<String> command = new ArrayList<String>();
        command.add("crontab");
        if (args != null) {
            command.addAll(args);
        }
        try {
            return ProcessUtils.checkCall(command);
        } catch (IOException e) {
            // Ignore exit code 1, when the crontab is not defined for the user.
            if (e.getMessage().contains("no crontab for")) {
                return "";
            }
            throw e;
        }
    }

    /**
     * Parse the crontab into crontab entry
     * 
     * @param data
     *            the crontab data (as output by `crontab -l`)
     * @return a crontab instance.
     */
    protected static Crontab parse(String data) {
        String[] lines = data.split("\n");
        List<CrontabEntry> entries = new ArrayList<CrontabEntry>();
        for (String line : lines) {
            // Skip some invalid lines.
            if (line.startsWith("DO NOT EDIT THIS FILE") || line.startsWith("no crontab for")) {
                continue;
            }
            entries.add(new CrontabEntry(line));
        }
        return new Crontab(entries);
    }

    /**
     * Read a crontab for current user.
     * 
     * @return the crontab
     * @throws IOException
     *             if an I/O error occurs
     */
    public static Crontab readAll() throws IOException {
        String data = execute(Arrays.asList("-l"));
        return parse(data);
    }

    /**
     * Remove the given crontab entry from crontab.
     * 
     * @param entry
     *            the entry to be removed.
     * @throws IOException
     */
    public static void removeEntry(CrontabEntry entry) throws IOException {
        Validate.notNull(entry);
        // Read current crontab.
        Crontab crontab = readAll();
        // Remove entry
        crontab.remove(entry);
        // Generate a temporary file.
        File file = File.createTempFile("minarca", "crontab");
        FileUtils.write(file, crontab.toString());
        // Install crontab
        execute(Arrays.asList(file.toString()));
        // Delete temporary file
        file.delete();
    }

    private final List<CrontabEntry> entries;

    /**
     * Create a new immutable instance of Crontab.
     * 
     * @param entries
     *            list of entries.
     */
    protected Crontab(List<CrontabEntry> entries) {
        Validate.notNull(this.entries = entries);
    }

    /**
     * Add cron tab entry.
     * 
     * @param entry
     *            the entry to be added.
     */
    public void add(CrontabEntry entry) {
        Validate.notNull(entry);
        this.entries.add(entry);
    }

    /**
     * Return list of crontab entries including comments.
     * 
     * @return the entries
     */
    public List<CrontabEntry> getAllEntries() {
        return new ArrayList<CrontabEntry>(this.entries);
    }

    /**
     * Return list of crontab entries (only jobs).
     * 
     * @return the entries
     */
    public List<CrontabEntry> getEntries() {
        List<CrontabEntry> list = new ArrayList<CrontabEntry>();
        for (CrontabEntry e : this.entries) {
            if (e.getComment() == null) {
                list.add(e);
            }
        }
        return list;
    }

    /**
     * Remove cron tab entry.
     * 
     * @param entry
     *            the entry to remove.
     */
    public void remove(CrontabEntry entry) {
        Validate.notNull(entry);
        if (!this.entries.remove(entry)) {
            throw new IllegalArgumentException();
        }
    }

    @Override
    public String toString() {
        StringBuffer buf = new StringBuffer();
        for (CrontabEntry e : this.entries) {
            buf.append(e.getLine());
            buf.append("\n");
        }
        return buf.toString();
    }

}
