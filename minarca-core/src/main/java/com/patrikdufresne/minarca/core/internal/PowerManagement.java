package com.patrikdufresne.minarca.core.internal;

import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;

import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;

/**
 * Power management class to abstract the OS details.
 * 
 * @author vmtest
 *
 */
public class PowerManagement {

    /**
     * Used to inhibit the the computer from sleeping
     */
    public static void inhibit() {
        if (SystemUtils.IS_OS_WINDOWS) {
            // Prevent Windows from going to sleep.
            int r = Kernel32.INSTANCE.SetThreadExecutionState(WinBase.ES_CONTINUOUS | WinBase.ES_SYSTEM_REQUIRED | WinBase.ES_AWAYMODE_REQUIRED);
            Validate.isTrue(r != 0, "call to SetThreadExecutionState return 0");
        }
        // TODO For Gnome/Linux
    }

    /**
     * Revert back the sleep mode.
     */
    public static void uninhibit() {
        if (SystemUtils.IS_OS_WINDOWS) {
            // Allow Windows to go to sleep.
            int r = Kernel32.INSTANCE.SetThreadExecutionState(WinBase.ES_CONTINUOUS);
            Validate.isTrue(r != 0, "call to SetThreadExecutionState return 0");
        }
        // TODO For Gnome/Linux
    }

}
