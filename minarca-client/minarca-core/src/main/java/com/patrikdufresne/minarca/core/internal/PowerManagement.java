package com.patrikdufresne.minarca.core.internal;

import org.apache.commons.lang3.SystemUtils;
import org.freedesktop.dbus.DBusAsyncReply;
import org.freedesktop.dbus.annotations.DBusInterfaceName;
import org.freedesktop.dbus.connections.impl.DBusConnection;
import org.freedesktop.dbus.connections.impl.DBusConnection.DBusBusType;
import org.freedesktop.dbus.exceptions.DBusException;
import org.freedesktop.dbus.interfaces.DBusInterface;
import org.freedesktop.dbus.types.UInt32;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;

/**
 * Power management class to abstract the OS details.
 * 
 * For Windows we are using SetThreadExecutionState native API.
 * 
 * For Linux we are using dbus gnome session API.
 * 
 * @see http://www.lucidelectricdreams.com/2011/06/disabling-screensaverlock-screen-on.html
 * @see https://people.gnome.org/~mccann/gnome-session/docs/gnome-session.html#org.gnome.SessionManager.Uninhibit
 * @see https://www.freedesktop.org/wiki/Software/systemd/inhibit/
 * 
 * @author Patrik Dufresne
 * 
 */
public class PowerManagement {

    @DBusInterfaceName("org.gnome.SessionManager")
    private interface SessionManager extends DBusInterface {

        UInt32 Inhibit(String app_id, UInt32 toplevel_xid, String reason, UInt32 flags);

        UInt32 Uninhibit(UInt32 inhibit_cookie);

        boolean IsInhibited(UInt32 flags);

    }

    private static final transient Logger LOGGER = LoggerFactory.getLogger(PowerManagement.class);

    /**
     * Cookie return by Linux Gnome session inhibit.
     */
    private static UInt32 inhibitCookie;

    /**
     * Used to inhibit the the computer from sleeping
     */
    public static void inhibit() {
        if (SystemUtils.IS_OS_WINDOWS) {
            inhibitWin32();
        } else {
            inhibitLinux();
        }
    }

    private static void inhibitLinux() {
        try {
            DBusConnection session = DBusConnection.getConnection(DBusBusType.SESSION);
            DBusInterface proxy = session.getRemoteObject("org.gnome.SessionManager", "/org/gnome/SessionManager", SessionManager.class);
            DBusAsyncReply<?> reply = session.callMethodAsync(proxy, "Inhibit", "minarca", new UInt32(0), "Inhibiting", INHIBIT_FLAG_4);
            int timeout = 1000;
            while (!reply.hasReply() && timeout > 0) {
                try {
                    Thread.sleep(10);
                    timeout -= 10;
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
            inhibitCookie = (UInt32) reply.getReply();
        } catch (DBusException e) {
            LOGGER.warn("inhibit gnome session manager failed", e);
        }
    }

    private static void inhibitWin32() {
        // Prevent Windows from going to sleep.
        int r = Kernel32.INSTANCE.SetThreadExecutionState(WinBase.ES_CONTINUOUS | WinBase.ES_SYSTEM_REQUIRED | WinBase.ES_AWAYMODE_REQUIRED);
        if (r == 0) {
            LOGGER.warn("call to SetThreadExecutionState(ES_CONTINUOUS|ES_SYSTEM_REQUIRED|ES_AWAYMODE_REQUIRED) return 0");
        }
    }

    public static boolean isInhibited() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return isInhibitedWin32();
        }
        return isInhibitedLinux();

    }

    /**
     * 4: Inhibit suspending the session or computer
     */
    private static final UInt32 INHIBIT_FLAG_4 = new UInt32(4);

    private static boolean isInhibitedLinux() {
        // Check if inhibited
        // dbus-send --session --dest=org.gnome.SessionManager --type=method_call --print-reply
        // --reply-timeout=20000 /org/gnome/SessionManager org.gnome.SessionManager.IsInhibited uint32:2

        // Get list of inhibitors
        // dbus-send --session --dest=org.gnome.SessionManager --type=method_call --print-reply
        // --reply-timeout=20000 /org/gnome/SessionManager org.gnome.SessionManager.GetInhibitors
        try {
            DBusConnection session = DBusConnection.getConnection(DBusBusType.SESSION);
            DBusInterface proxy = session.getRemoteObject("org.gnome.SessionManager", "/org/gnome/SessionManager", SessionManager.class);
            DBusAsyncReply<?> isInhibited = session.callMethodAsync(proxy, "IsInhibited", INHIBIT_FLAG_4);
            int timeout = 1000;
            while (!isInhibited.hasReply() && timeout > 0) {
                try {
                    Thread.sleep(10);
                    timeout -= 10;
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
            return (Boolean) isInhibited.getReply();
        } catch (DBusException e) {
            LOGGER.warn("inhibit gnome session manager failed", e);
        }
        return false;
    }

    private static boolean isInhibitedWin32() {
        int r = Kernel32.INSTANCE.SetThreadExecutionState(WinBase.ES_CONTINUOUS);
        if (r != 0) {
            Kernel32.INSTANCE.SetThreadExecutionState(r);
        }
        return r == (WinBase.ES_CONTINUOUS | WinBase.ES_SYSTEM_REQUIRED | WinBase.ES_AWAYMODE_REQUIRED);
    }

    /**
     * Revert back the sleep mode.
     */
    public static void uninhibit() {
        if (SystemUtils.IS_OS_WINDOWS) {
            uninhibitWin32();
        } else {
            uninhibitLinux();
        }
    }

    private static void uninhibitLinux() {
        try {
            DBusConnection session = DBusConnection.getConnection(DBusBusType.SESSION);
            DBusInterface proxy = session.getRemoteObject("org.gnome.SessionManager", "/org/gnome/SessionManager", SessionManager.class);
            DBusAsyncReply<?> reply = session.callMethodAsync(proxy, "Uninhibit", inhibitCookie);
            int timeout = 1000;
            while (!reply.getCall().hasReply() && timeout > 0) {
                try {
                    Thread.sleep(10);
                    timeout -= 10;
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
        } catch (DBusException e) {
            LOGGER.warn("inhibit gnome session return an error", e);
        }
    }

    private static void uninhibitWin32() {
        // Allow Windows to go to sleep.
        int r = Kernel32.INSTANCE.SetThreadExecutionState(WinBase.ES_CONTINUOUS);
        if (r == 0) {
            LOGGER.warn("call to SetThreadExecutionState(ES_CONTINUOUS) return 0");
        }
    }

}
