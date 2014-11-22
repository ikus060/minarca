package com.patrikdufresne.minarca.core.internal;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Scanner;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang.StringUtils;
import org.apache.commons.lang.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

/**
 * Wrapper arround "schtasks" command line.
 * 
 * @author ikus060-vm
 *
 */
public class Schtasks {

	private static class SchTaskEntry {

		private static final String TASKNAME = "TaskName";

		// ["HostName", "TaskName", "Next Run Time", "Status", "Logon Mode",
		// "Last Run Time", "Last Result", "Author", "Task To Run", "Start In",
		// "Comment", "Scheduled Task State", "Idle Time", "Power Management",
		// "Run As User", "Delete Task If Not Rescheduled",
		// "Stop Task If Runs X Hours and X Mins", "Schedule", "Schedule Type",
		// "Start Time", "Start Date", "End Date", "Days", "Months",
		// "Repeat: Every", "Repeat: Until: Time", "Repeat: Until: Duration",
		// "Repeat: Stop If Still Running"]

		Map<String, String> data;

		private SchTaskEntry(Map<String, String> data) {
			Validate.notNull(this.data = data);
		}

		public String get(String key) {
			return this.data.get(key);
		}

		public String getTaskname() {
			return get(TASKNAME);
		}

		@Override
		public String toString() {
			return "SchTaskEntry [taskname=" + getTaskname() + "]";
		}

	}

	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(Schtasks.class);

	/**
	 * Remove leadin and ending quote.
	 * 
	 * @param string
	 * @return
	 */
	private static String trimQuote(String string) {
		int len = string.length();
		int st = 0;
		int off = 0; /* avoid getfield opcode */
		char[] val = string.toCharArray(); /* avoid getfield opcode */

		while ((st < len) && (val[off + st] == '"')) {
			st++;
		}
		while ((st < len) && (val[off + len - 1] == '"')) {
			len--;
		}
		return ((st > 0) || (len < string.length())) ? string
				.substring(st, len) : string;
	}

	public Schtasks() {

	}

	/**
	 * Create a new schedule tasks
	 * 
	 * <pre>
	 * SCHTASKS /Create [/S system [/U username [/P password]]]
	 *     [/RU username [/RP password]] /SC schedule [/MO modifier] [/D day]
	 *     [/I idletime] /TN taskname /TR taskrun [/ST starttime] [/M months]
	 *     [/SD startdate] [/ED enddate]
	 * </pre>
	 * 
	 * @throws APIException
	 * 
	 * @see http 
	 *      ://www.windowsnetworking.com/kbase/WindowsTips/WindowsXP/AdminTips
	 *      /Utilities/XPschtaskscommandlineutilityreplacesAT.exe.html
	 */
	public void create(String taskname, String command) throws APIException {
		String data = execute("/Create", "/SC", "HOURLY", "/TN", taskname,
				"/TR", command);
		if (!data.contains("SUCCESS")) {
			throw new APIException("fail to schedule task");
		}
	}

	/**
	 * Delete the task named <code>taskname</code>.
	 * 
	 * @param taskname
	 *            the task to be deleted.
	 * @throws APIException
	 */
	public boolean delete(String taskname) throws APIException {
		String data = execute("/Delete", "/F", "/TN", taskname);
		return data.contains("SUCCESS");
	}

	/**
	 * Used to execute the command.
	 * 
	 * @throws APIException
	 */
	private String execute(List<String> args) throws APIException {
		List<String> command = new ArrayList<String>();
		command.add("schtasks.exe");
		if (args != null) {
			command.addAll(args);
		}
		LOGGER.debug("executing {}", StringUtils.join(command, " "));
		try {
			Process p = new ProcessBuilder().command(command)
					.redirectErrorStream(true).start();
			StreamHandler sh = new StreamHandler(p);
			sh.start();
			p.waitFor();
			return sh.getOutput();
		} catch (IOException e) {
			throw new APIException("fail to create subprocess", e);
		} catch (InterruptedException e) {
			// Swallow. Should no happen
			LOGGER.warn("process interupted", e);
			Thread.currentThread().interrupt();
		}
		return null;
	}

	/**
	 * Used to execute the command.
	 * 
	 * @param args
	 * @return
	 * @throws APIException
	 */
	private String execute(String... args) throws APIException {
		return execute(Arrays.asList(args));
	}

	/**
	 * Query the task list.
	 * 
	 * @throws APIException
	 */
	public List<SchTaskEntry> query() throws APIException {
		return internalQuery(null);
	}

	private List<SchTaskEntry> internalQuery(String taskname)
			throws APIException {
		String data;
		if (taskname != null) {
			// Query a specific taskname.
			data = execute("/Query", "/FO", "CSV", "/V", "/TN", taskname);
		} else {
			data = execute("/Query", "/FO", "CSV", "/V");
		}
		// Read the first line
		Scanner scanner = new Scanner(data);
		if (!scanner.hasNextLine()) {
			return null;
		}
		List<SchTaskEntry> list = new ArrayList<Schtasks.SchTaskEntry>();
		String line = scanner.nextLine();
		String[] columns = line.split(",");
		while (scanner.hasNextLine()) {
			Map<String, String> map = new LinkedHashMap<String, String>();
			line = scanner.nextLine();
			String[] values = line.split(",");
			if (Arrays.equals(columns, values)) {
				continue;
			}
			for (int i = 0; i < columns.length && i < values.length; i++) {
				map.put(trimQuote(columns[i]), trimQuote(values[i]));
			}
			SchTaskEntry task = new SchTaskEntry(map);
			list.add(task);
		}
		scanner.close();
		return list;
	}

	/**
	 * Query the given taskname.
	 * 
	 * @param taskname
	 * @throws APIException
	 */
	public SchTaskEntry query(String taskname) throws APIException {
		// Find a matching taskname.
		for (SchTaskEntry t : internalQuery(taskname)) {
			if (t.getTaskname() != null && t.getTaskname().endsWith(taskname)) {
				return t;
			}
		}
		return null;
	}

	/**
	 * Check if a task with the given name exists.
	 * 
	 * @param taskName
	 *            the task name.
	 * @return True if exists.
	 */
	public boolean exists(String taskname) {
		try {
			return query(taskname) != null;
		} catch (APIException e) {
			return false;
		}
	}
}
