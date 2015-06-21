/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.layout.GridLayoutFactory;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.CTabFolder;
import org.eclipse.swt.custom.CTabItem;
import org.eclipse.swt.events.DisposeEvent;
import org.eclipse.swt.events.DisposeListener;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.forms.widgets.Form;
import org.eclipse.ui.forms.widgets.FormText;
import org.eclipse.ui.forms.widgets.TableWrapLayout;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.GlobPattern;
import com.patrikdufresne.minarca.core.internal.Scheduler.TaskInfo;

/**
 * This is the main windows of the application used to configure the backup.
 * 
 * @author Patrik Dufresne
 * 
 */
public class PreferenceDialog extends Dialog {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(PreferenceDialog.class);

    /**
     * Create an executor service to asynchronously update the UI.
     */
    private ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();

    private FormText backupinfo;

    private Button backupNowButton;

    private Button excludeSysFilesButton;

    private AppFormToolkit ft;

    private Button includeDefaultsButton;

    /**
     * Create a new preference dialog.
     */
    public PreferenceDialog() {
        super((Shell) null);
    }

    /**
     * Asynchronously check backup info.
     * 
     * @param backupinfo
     */
    private void asynchCheckBackupInfo(final FormText backupinfo, final Button backupnow) {
        executor.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {
                // Then check link.
                checkBackupInfo(backupinfo, backupnow);
            }
        }, 1000, 15000, TimeUnit.MILLISECONDS);
    }

    /**
     * Asynchronously check link with minarca.
     * 
     * @param formtext
     */
    private void asynchCheckLink(final FormText formtext) {
        executor.schedule(new Runnable() {
            @Override
            public void run() {
                // Then check link.
                checkLink(formtext);
            }
        }, 1000, TimeUnit.MILLISECONDS);
    }

    /**
     * Handle close button.
     */
    @Override
    protected void buttonPressed(int buttonId) {
        if (IDialogConstants.CLOSE_ID == buttonId) {
            setReturnCode(IDialogConstants.CLOSE_ID);
            close();
        } else {
            super.buttonPressed(buttonId);
        }
    }

    /**
     * Check backup info and update the UI accordingly.
     * 
     * @param backupinfo
     */
    private void checkBackupInfo(final FormText backupinfo, final Button backupnow) {
        Validate.notNull(backupinfo);
        Validate.notNull(backupnow);
        // Get backup info.
        String msg;
        Boolean running1;
        try {
            TaskInfo info = API.instance().getScheduleTaskInfo();
            running1 = info.isRunning();
            if (running1) {
                msg = _("Backup is running.");
            } else {
                msg = _("Backup is not running.");
            }
        } catch (APIException e) {
            msg = "";
            running1 = false;
        }
        // Update UI
        final String text = msg;
        final Boolean running2 = running1;
        Display.getDefault().asyncExec(new Runnable() {
            @Override
            public void run() {
                if (!backupinfo.isDisposed()) {
                    backupinfo.setText(text, true, true);
                }
                if (!backupnow.isDisposed()) {
                    backupnow.setEnabled(!running2);
                }
            }
        });
    }

    /**
     * Asynchronously check link with minarca.
     * 
     * @param textlink
     */
    private void checkLink(final FormText formtext) {
        Validate.notNull(formtext);
        // Test the connectivity with minarca using test.
        String msg;
        try {
            API.instance().testServer();
            msg = _("This computer is linked to minarca.");
        } catch (APIException e) {
            msg = _("This computer doesn't seams to be linked with minarca!");
        }
        final String text = msg;
        Display.getDefault().asyncExec(new Runnable() {
            @Override
            public void run() {
                if (!formtext.isDisposed()) {
                    formtext.setText(text, true, true);
                }
            }
        });
    }

    /**
     * Sets dialog title
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(_("Minarca preferences"));
    }

    /**
     * Create a single Close button
     */
    @Override
    protected void createButtonsForButtonBar(Composite parent) {
        createButton(parent, IDialogConstants.CLOSE_ID, IDialogConstants.CLOSE_LABEL, true);
    }

    @Override
    protected Control createDialogArea(Composite parent) {

        this.ft = new AppFormToolkit(parent.getDisplay());

        CTabFolder tab = this.ft.createCTabFolder(parent);
        tab.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, true));

        // Create General tab
        CTabItem generalItem = new CTabItem(tab, SWT.NONE);
        generalItem.setText(_("General"));
        generalItem.setControl(createPageGeneralContents(tab));

        // Create include exclude tab
        CTabItem patternsItem = new CTabItem(tab, SWT.NONE);
        patternsItem.setText(_("Selective backup"));
        patternsItem.setControl(createPagePatternsContents(tab));

        // Create include exclude tab
        CTabItem aboutItem = new CTabItem(tab, SWT.NONE);
        aboutItem.setText(_("About"));
        aboutItem.setControl(createPageAboutContents(tab));

        // Separator
        Label l = new Label(parent, SWT.SEPARATOR | SWT.HORIZONTAL);
        l.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));

        // Add dispose listener
        parent.addDisposeListener(new DisposeListener() {
            @Override
            public void widgetDisposed(DisposeEvent arg0) {
                handleDispose();
            }
        });

        return tab;
    }

    /**
     * Called when the dialog is about to be disposed.
     */
    protected void handleDispose() {
        // Stop the executor service.
        if (this.executor != null) {
            this.executor.shutdown();
        }
        this.executor = null;
    }

    /**
     * Create content of about tab.
     * 
     * @param parent
     * @return
     */
    private Control createPageAboutContents(Composite parent) {
        Form form = this.ft.createForm(parent);
        form.getBody().setLayout(GridLayoutFactory.swtDefaults().margins(15, 15).create());
        form.setLayoutData(new GridData(GridData.FILL_BOTH));
        Composite comp = form.getBody();

        // App name
        FormText appNameText = this.ft.createFormText(comp, "<h1>" + Display.getAppName() + "</h1>", false);
        appNameText.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // App icon
        Label icon = this.ft.createLabel(comp, null);
        icon.setImage(JFaceResources.getImage(Images.MINARCA_128_PNG));
        icon.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // App name
        FormText appVersionText = this.ft.createFormText(comp, "<h4>" + Display.getAppVersion() + "</h4>", false);
        appVersionText.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // App description
        FormText appDescText = this.ft.createFormText(comp, _("minarca is an all integrated online backup solution."), false);
        appDescText.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // App copyright
        FormText appCopyrightText = this.ft.createFormText(comp, _("Copyright © 2014 - Patrik Dufresne Service Logiciel"), false);
        appCopyrightText.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // Application web site
        FormText websiteText = this.ft.createFormText(comp, _("http://www.patrikdufresne.com/en/minarca/"), false);
        websiteText.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // Minarca link
        FormText minarcaWebSiteText = this.ft.createFormText(comp, "https://www.minarca.net/", false);
        minarcaWebSiteText.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        return form;
    }

    /**
     * Create content of general tab.
     * 
     * @param parent
     * @return
     */
    private Control createPageGeneralContents(Composite parent) {

        Form form = this.ft.createForm(parent);
        form.getBody().setLayout(GridLayoutFactory.swtDefaults().margins(15, 15).create());
        form.setLayoutData(new GridData(GridData.FILL_BOTH));
        Composite comp = form.getBody();
        TableWrapLayout layout = new TableWrapLayout();
        layout.topMargin = layout.rightMargin = layout.bottomMargin = layout.leftMargin = 15;
        layout.verticalSpacing = layout.horizontalSpacing = 15;
        comp.setLayout(layout);

        // Account section
        this.ft.createFormText(comp, "<h3>" + _("Account") + "</h3>", false);

        // General information
        String text = _("Username: ");
        text += "<b>" + API.instance().getUsername() + "</b><br/>";
        text += _("Computer name: ");
        text += "<b>" + API.instance().getComputerName() + "</b><br/>";
        text += _("Fingerprint: ");
        text += "<b>" + API.instance().getIdentityFingerPrint() + "</b><br/>";
        this.ft.createFormText(comp, text, false);

        // Check link
        text = _("Checking link...");
        FormText textlink = this.ft.createFormText(comp, text, false);

        // Unlink button
        Button unlinkButton = this.ft.createButton(comp, _("Unlink this computer..."), SWT.PUSH);
        unlinkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleUnlinkComputer();
            }
        });

        // Backup info
        this.ft.createFormText(comp, "<h3>" + _("Backup information") + "</h3>", false);
        text = "<a href='" + API.instance().getBrowseUrl() + "'>" + _("Browse backup data") + "</a>";
        this.ft.createFormText(comp, text, false);

        // General information
        text = _("Checking if backup is running...");
        this.backupinfo = this.ft.createFormText(comp, text, false);

        // Backup now button
        this.backupNowButton = this.ft.createButton(comp, _("Backup now"), SWT.PUSH);
        this.backupNowButton.setEnabled(false);
        this.backupNowButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleBackupNow();
            }
        });

        // Asyn update
        asynchCheckLink(textlink);
        asynchCheckBackupInfo(this.backupinfo, this.backupNowButton);

        // TODO General information about backup:
        // TODO Last backup date.
        // TODO Running.
        // TODO Disk usage.

        return form;
    }

    /**
     * Create content of include exclude patterns.
     * 
     * @param parent
     * @return
     */
    private Control createPagePatternsContents(Composite parent) {

        Form form = this.ft.createForm(parent);
        form.setLayoutData(new GridData(GridData.FILL_BOTH));
        Composite comp = form.getBody();
        TableWrapLayout layout = new TableWrapLayout();
        layout.topMargin = layout.rightMargin = layout.bottomMargin = layout.leftMargin = 15;
        layout.verticalSpacing = layout.horizontalSpacing = 15;
        comp.setLayout(layout);

        /*
         * Include Patterns
         */
        this.ft.createFormText(comp, "<h3>" + _("What to backup ?") + "</h3>", false);

        // Includes defaults
        boolean includeDefaults = API.instance().getIncludes().containsAll(GlobPattern.includesDefault());
        this.includeDefaultsButton = this.ft.createButton(comp, _("Personal files (recommended)"), SWT.CHECK);
        this.includeDefaultsButton.setSelection(includeDefaults);
        this.includeDefaultsButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleIncludeDetaults(e);
            }
        });

        /*
         * Excludes patterns
         */
        this.ft.createFormText(comp, "<h3>" + _("Ignore") + "</h3>", false);

        List<GlobPattern> excludes = API.instance().getExcludes();
        boolean excludeSysFiles = excludes.containsAll(GlobPattern.excludesSystem());
        boolean excludeDownloads = excludes.containsAll(GlobPattern.excludesDownloads());

        // Excludes defaults
        this.excludeSysFilesButton = this.ft.createButton(comp, _("Ignore operating system files (recommended)"), SWT.CHECK);
        this.excludeSysFilesButton.setSelection(excludeSysFiles);
        this.excludeSysFilesButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleExcludeDetaults(e, GlobPattern.excludesSystem());
            }
        });

        // Excludes
        this.excludeSysFilesButton = this.ft.createButton(comp, _("Ignore download folder (recommended)"), SWT.CHECK);
        this.excludeSysFilesButton.setSelection(excludeDownloads);
        this.excludeSysFilesButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleExcludeDetaults(e, GlobPattern.excludesDownloads());
            }
        });

        // Advance button
        Button advanceButton = this.ft.createButton(comp, _("Advance..."), SWT.PUSH);
        advanceButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleAdvancePatterns();
            }
        });

        return form;
    }

    /**
     * Define dialog size.
     */
    @Override
    protected Point getInitialSize() {
        // Sets fixed window size.
        if (SystemUtils.IS_OS_LINUX) {
            return new Point(450, 550);
        }
        return new Point(425, 500);
    }

    /**
     * Called when user want to select advance filter.
     */
    protected void handleAdvancePatterns() {
        List<GlobPattern> excludes = API.instance().getExcludes();
        List<GlobPattern> defaultExcludes = new ArrayList<GlobPattern>();
        boolean excludeSysFiles = excludes.containsAll(GlobPattern.excludesSystem());
        if (excludeSysFiles) {
            defaultExcludes.addAll(GlobPattern.excludesSystem());
        }
        boolean excludeDownloads = excludes.containsAll(GlobPattern.excludesDownloads());
        if (excludeDownloads) {
            defaultExcludes.addAll(GlobPattern.excludesDownloads());
        }

        // Open a dialog to edit filters.
        IncludesDialog dlg = new IncludesDialog(this.getShell());
        dlg.setIncludes(API.instance().getIncludes());
        dlg.setExcludes(excludes);
        dlg.setDefaultIncludes(GlobPattern.includesDefault());
        dlg.setDefaultExcludes(defaultExcludes);
        if (dlg.open() != Window.OK) {
            return;
        }
        try {
            API.instance().setIncludes(dlg.getIncludes());
            API.instance().setExcludes(dlg.getExcludes());
        } catch (APIException e) {
            showError(e);
        }
    }

    /**
     * Start backup now.
     */
    protected void handleBackupNow() {
        // Check if backup is running
        Boolean running;
        try {
            running = API.instance().getScheduleTaskInfo().isRunning();
        } catch (APIException e) {
            running = false;
        }
        if (Boolean.TRUE.equals(running)) {
            DetailMessageDialog.openInformation(
                    this.getShell(),
                    _("Backup now"),
                    _("Backup is already running!"),
                    _("You can't start another backup process because there is one already running."),
                    (String) null);
            return;
        }

        // Show a confirmation message.
        DetailMessageDialog dlg = DetailMessageDialog
                .openYesNoQuestion(
                        this.getShell(),
                        _("Backup now"),
                        _("Do you want to backup your system?"),
                        _("You are about to backup your system to minarca. This operation may take some time. While this operation is running you may safely close the minarca application."),
                        null);
        if (dlg.getReturnCode() != IDialogConstants.YES_ID) {
            LOGGER.info("backup cancel by user");
            return;
        }

        // Unlink this computer.
        try {
            API.instance().runBackup();
        } catch (APIException e) {
            DetailMessageDialog.openError(this.getShell(), _("Error"), _("Can't backup this computer!"), _("An error occurred while backuping this computer."));
        }

        // Asynchronously update the interface.
        asynchCheckBackupInfo(this.backupinfo, this.backupNowButton);

    }

    /**
     * Called when user select or unselect the default excludes.
     * 
     * @param event
     */
    protected void handleExcludeDetaults(SelectionEvent event, List<GlobPattern> list) {
        Set<GlobPattern> excludes = new LinkedHashSet<GlobPattern>(API.instance().getExcludes());
        if (this.excludeSysFilesButton.getSelection()) {
            excludes.addAll(list);
        } else {
            excludes.removeAll(list);
        }
        try {
            API.instance().setExcludes(new ArrayList<GlobPattern>(excludes));
        } catch (APIException e) {
            showError(e);
        }
    }

    /**
     * Called when user select or un-select "include defaults".
     */
    protected void handleIncludeDetaults(SelectionEvent event) {
        Set<GlobPattern> includes = new LinkedHashSet<GlobPattern>(API.instance().getIncludes());
        if (this.includeDefaultsButton.getSelection()) {
            includes.addAll(GlobPattern.includesDefault());
        } else {
            includes.removeAll(GlobPattern.includesDefault());
        }
        try {
            API.instance().setIncludes(new ArrayList<GlobPattern>(includes));
        } catch (APIException e) {
            showError(e);
        }
    }

    /**
     * Called to unlink this computer.
     */
    protected void handleUnlinkComputer() {

        // Show a confirmation message.
        DetailMessageDialog dlg = DetailMessageDialog.openYesNoQuestion(
                this.getShell(),
                _("Confirm unlink"),
                _("Are you sure you want to unlink this computer from minarca?"),
                _("You are about to unlink this computer from minarca. This "
                        + "computer will no longer backup it self. Previous "
                        + "backup data will not be lost."),
                null);
        if (dlg.getReturnCode() != IDialogConstants.YES_ID) {
            LOGGER.info("unlink opperation cancel by user");
            return;
        }

        // Unlink this computer.
        try {
            API.instance().unlink();
        } catch (APIException e) {
            DetailMessageDialog.openError(this.getShell(), _("Error"), _("Can't unlink this computer!"), _("An error occurred while unlinking this computer."));
        }

        // Then close this dialog to open the setup dialog.
        close();

    }

    /**
     * Used to display error message to user when it's impossible to save configuration.
     * 
     * @param e
     */
    private void showError(APIException e) {
        LOGGER.error("error updating configuration", e);
        DetailMessageDialog.openError(
                this.getShell(),
                _("Error"),
                _("Error updating configuration"),
                _("Can't change the configuration for unknown reason. If the problem persists, try re-installing minarca."));
    }
}
