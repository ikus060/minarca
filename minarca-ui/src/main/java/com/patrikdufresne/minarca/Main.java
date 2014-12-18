/**
 * Copyright(C) 2013 Patrik Dufresne Service Logiciel <info@patrikdufresne.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca;

import static com.patrikdufresne.minarca.Localized._;

import java.util.ArrayList;
import java.util.List;

import org.apache.commons.lang3.SystemUtils;
import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.jface.resource.ImageRegistry;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.util.ILogger;
import org.eclipse.jface.util.Policy;
import org.eclipse.jface.window.Window;
import org.eclipse.jface.window.WindowManager;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.widgets.Display;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.NotConfiguredException;
import com.patrikdufresne.minarca.ui.PreferenceDialog;
import com.patrikdufresne.minarca.ui.SetupDialog;

/**
 * This class is the main entry point to the software.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Main {

    public static final String MINARCA_16_PNG = "minarca_16.png";
    public static final String MINARCA_32_PNG = "minarca_32.png";
    public static final String MINARCA_PNG = "minarca.png";

    static final transient Logger LOGGER = LoggerFactory.getLogger(Main.class);

    /**
     * Return the current version.
     * 
     * @return
     */
    public static String getCurrentVersion() {
        // Get the version from the package manifest
        String version = Main.class.getPackage().getImplementationVersion();
        if (version == null) {
            return "DEV";
        }
        return version;
    }

    /**
     * This function is the main entry point.
     * 
     * @param args
     */
    public static void main(String[] args) {
        new Main().start(args);
    }

    /**
     * This function is updating the JFace Policy error handler.
     */
    protected static void updateJFacePolicy() {
        Policy.setLog(new ILogger() {

            @Override
            public void log(IStatus status) {
                switch (status.getSeverity()) {
                case IStatus.OK:
                case IStatus.INFO:
                    if (status.getException() == null) {
                        LOGGER.info(status.getMessage());
                    } else {
                        LOGGER.info(status.getMessage(), status.getException());
                    }
                    break;
                case IStatus.WARNING:
                    if (status.getException() == null) {
                        LOGGER.warn(status.getMessage());
                    } else {
                        LOGGER.warn(status.getMessage(), status.getException());
                    }
                    break;
                case IStatus.ERROR:
                    if (status.getException() == null) {
                        LOGGER.error(status.getMessage());
                    } else {
                        LOGGER.error(status.getMessage(), status.getException());
                    }
                    break;
                }
                System.err.println(status.getMessage());
                if (status.getException() != null) {
                    status.getException().printStackTrace(System.err);
                }
            }
        });
    }

    protected void setDefaultImages() {
        // Register image
        ImageRegistry ir = JFaceResources.getImageRegistry();
        ir.put(MINARCA_16_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_16_PNG));
        ir.put(MINARCA_32_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_32_PNG));
        ir.put(MINARCA_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_PNG));

        List<Image> images = new ArrayList<Image>();
        images.add(ir.get(MINARCA_PNG));
        images.add(ir.get(MINARCA_32_PNG));
        images.add(ir.get(MINARCA_16_PNG));

        // Sets images.
        Window.setDefaultImages(images.toArray(new Image[images.size()]));
    }

    /**
     * This function start the application.
     * 
     * @param args
     */
    private void start(String[] args) {

        Display.setAppName(_("minarca"));
        Display.setAppVersion(getCurrentVersion());
        final Display display = new Display();

        // Sets default windows images
        setDefaultImages();

        // Update logger
        updateJFacePolicy();

        // Check OS
        if (!(SystemUtils.IS_OS_WINDOWS || SystemUtils.IS_OS_LINUX)) {
            MessageDialog.openError(null, Display.getAppName(), _("Minarca doesn't support you OS. " + "This application will close."));
            return;
        }

        WindowManager winManager = null;
        try {
            // Check configuration or re-configured
            if (!configure()) {
                return;
            }

            winManager = new WindowManager();
            // Open Main Window
            PreferenceDialog win = new PreferenceDialog();
            win.setWindowManager(winManager);
            win.open();
            // Event loop
            while (winManager.getWindowCount() > 0) {
                try {
                    if (!display.readAndDispatch()) display.sleep();
                } catch (RuntimeException e) {
                    Policy.getStatusHandler().show(new Status(IStatus.ERROR, Display.getAppName(), e.getMessage(), e), null);
                }
            }
        } catch (Exception e) {
            LOGGER.error("unknown error", e);
            MessageDialog.openWarning(null, Display.getAppName(), e.getMessage());
        } finally {
            if (winManager != null) {
                winManager.close();
            }
            display.dispose();
        }

    }

    /**
     * Check if the application is configured. If not show a setup dialog. If miss configured try to repair.
     * 
     * @return True if configured or miss configured. False if not configured and user cancel configuration.
     */
    private boolean configure() {
        // Check if configured.
        try {
            LOGGER.debug("checking minarca configuration");
            API.INSTANCE.checkConfig();
            LOGGER.debug("configuration is OK");
        } catch (NotConfiguredException e) {
            // If not configured, show wizard.
            LOGGER.debug("not configured -- show setup dialog");
            if (!SetupDialog.open(null)) {
                // If user cancel, lose application.
                return false;
            }
        } catch (MissConfiguredException e) {
            // The configuration is broken. Ask use if we can fix it.
            LOGGER.debug("miss-configured -- ask to repair", e);
            if (MessageDialog.openQuestion(null, Display.getAppName(), _("Your minarca installation seams broken! "
                    + "Do you want to restore default configuration? "
                    + "If you answer Yes, all your personal configuration will be lost. "
                    + "If you answer no, this application may misbehave."))) {
                try {
                    LOGGER.debug("repair configuration");
                    API.INSTANCE.defaultConfig();
                } catch (APIException e1) {
                    MessageDialog.openWarning(null, Display.getAppName(), _("Can't repair minarca configuration. "
                            + "If the problem persist, you may try to reinstall minarca."));
                }
            } else {
                return true;
            }
        } catch (APIException e) {
            return false;
        }
        return true;
    }
}
