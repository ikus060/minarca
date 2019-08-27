/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.ui.Localized._;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.concurrent.BasicThreadFactory;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.viewers.ComboViewer;
import org.eclipse.jface.viewers.ISelectionChangedListener;
import org.eclipse.jface.viewers.LabelProvider;
import org.eclipse.jface.viewers.SelectionChangedEvent;
import org.eclipse.jface.viewers.StructuredSelection;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.DisposeEvent;
import org.eclipse.swt.events.DisposeListener;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.program.Program;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.forms.FormColors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.fontawesome.FontAwesome;
import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.LastResult;
import com.patrikdufresne.minarca.core.Schedule;
import com.patrikdufresne.minarca.core.Status;

/**
 * This is the main windows of the application used to configure the backup.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SettingsDialog extends Dialog {

    /**
     * Button id for About button.
     */
    private static final int ABOUT_ID = IDialogConstants.CLIENT_ID;

    /**
     * Label for about button.
     */
    private static final String ABOUT_LABEL = _("About");

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SettingsDialog.class);

    /**
     * Symbolic name for warning background color.
     */
    private static final String WARN_BACKGROUNG = "WARN_BACKGROUNG";

    /**
     * Create an executor service to asynchronously update the UI.
     */
    private ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor(new BasicThreadFactory.Builder().namingPattern(
            "scheduled-ui-update-%d").build());

    private AppFormToolkit ft;

    private CListItem lastruntimeItem;

    private ComboViewer scheduleCombo;

    private CListItem statusItem;

    private Button stopStartButton;

    private Button unlinkButton;

    /**
     * Create a new preference dialog.
     */
    public SettingsDialog() {
        super((Shell) null);
    }

    /**
     * Called when user press about button.
     */
    private void aboutPressed() {
        AboutDialog dlg = new AboutDialog(getShell());
        dlg.open();
    }

    /**
     * Handle close button.
     */
    @Override
    protected void buttonPressed(int buttonId) {
        if (IDialogConstants.CLOSE_ID == buttonId) {
            setReturnCode(IDialogConstants.CLOSE_ID);
            close();
        } else if (IDialogConstants.HELP_ID == buttonId) {
            helpPressed();
        } else if (ABOUT_ID == buttonId) {
            aboutPressed();
        } else {
            super.buttonPressed(buttonId);
        }
    }

    /**
     * Asynchronously check backup info.
     */
    private void checkBackupStatus() {
        executor.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {

                // Get backup info.
                final Status state = API.instance().status();

                // Update UI
                Display.getDefault().asyncExec(new Runnable() {
                    @Override
                    public void run() {
                        if (lastruntimeItem.isDisposed()) {
                            return;
                        }

                        // Update label button according to task state.
                        if (LastResult.UNKNOWN.equals(state.getLastResult())) {
                            stopStartButton.setEnabled(false);
                        } else {
                            stopStartButton.setEnabled(true);
                            stopStartButton.setText(LastResult.RUNNING.equals(state.getLastResult()) ? _("Stop backup") : _("Start backup"));
                        }

                        // Update help text with Success or Failure
                        // Update value with last date.
                        lastruntimeItem.setValue(state.getLocalized());
                        switch (state.getLastResult()) {
                        case RUNNING:
                        case SUCCESS:
                            ft.setSkinClass(lastruntimeItem, AppFormToolkit.CLASS_SUCESS);
                            break;
                        case FAILURE:
                        case HAS_NOT_RUN:
                        case STALE:
                        case INTERRUPT:
                        default:
                            ft.setSkinClass(lastruntimeItem, AppFormToolkit.CLASS_ERROR);
                        }

                    }
                });

            }
        }, 1, 1000, TimeUnit.MILLISECONDS);
    }

    /**
     * Asynchronously check link with minarca.
     * 
     * @param formtext
     */
    private void checkConnectivityStatus() {
        executor.schedule(new Runnable() {
            @Override
            public void run() {
                // Test the connectivity with minarca server using test-server.
                String text;
                boolean linked;
                try {
                    API.instance().testServer();
                    linked = true;
                    text = _("Connected");
                } catch (Exception e) {
                    LOGGER.warn("check link failed", e);
                    // TODO: Complete this to provide the right status: can't connect, refused, etc.
                    linked = false;
                    text = _("Unknown");
                }
                final String fText = text;
                final boolean fLinked = linked;
                Display.getDefault().asyncExec(new Runnable() {
                    @Override
                    public void run() {
                        if (statusItem.isDisposed()) {
                            return;
                        }

                        // Update the value of status item
                        statusItem.setValue(fText);

                        // Update the colour of the status.
                        ft.setSkinClass(statusItem, !fLinked ? AppFormToolkit.CLASS_ERROR : AppFormToolkit.CLASS_SUCESS);

                        // Update button enabled state.
                        unlinkButton.setEnabled(true);
                    }
                });
            }
        }, 1, TimeUnit.MILLISECONDS);
    }

    /**
     * Sets dialog title
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(Display.getAppName());
    }

    @Override
    protected Control createButtonBar(Composite parent) {
        Composite composite = new Composite(parent, SWT.NONE);
        GridLayout layout = new GridLayout();
        layout.marginWidth = 0;
        layout.marginHeight = 0;
        layout.horizontalSpacing = 0;
        composite.setLayout(layout);
        composite.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
        composite.setFont(parent.getFont());

        GridData data;

        // Create help button
        Button helpButton = createButton(composite, IDialogConstants.HELP_ID, IDialogConstants.HELP_LABEL, false);
        data = ((GridData) helpButton.getLayoutData());
        data.horizontalIndent = convertHorizontalDLUsToPixels(IDialogConstants.HORIZONTAL_MARGIN);
        if (FontAwesome.getFont() != null) {
            // Change text for icon.
            helpButton.setToolTipText(helpButton.getText());
            helpButton.setFont(FontAwesome.getFont());
            helpButton.setText(FontAwesome.question);
            // Update layout (to have a square button).
            Point minSize = helpButton.computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
            data.widthHint = data.heightHint = Math.max(minSize.y, minSize.x);
        }

        // Create about button
        Button aboutButton = createButton(composite, ABOUT_ID, ABOUT_LABEL, false);
        data = ((GridData) aboutButton.getLayoutData());
        if (FontAwesome.getFont() != null) {
            // Change text for icon.
            aboutButton.setToolTipText(aboutButton.getText());
            aboutButton.setFont(FontAwesome.getFont());
            aboutButton.setText(FontAwesome.info);
            // Update layout (to have a square button).
            Point minSize = aboutButton.computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
            data.widthHint = data.heightHint = Math.max(minSize.y, minSize.x);
        }

        // Create default button bar.
        Control buttonSection = super.createButtonBar(composite);
        ((GridData) buttonSection.getLayoutData()).grabExcessHorizontalSpace = true;
        return composite;
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
        ft = new AppFormToolkit(this.getShell().getDisplay(), true);
        Composite comp = ft.createComposite(parent);
        comp.setLayout(new GridLayout());
        comp.setLayoutData(new GridData(GridData.FILL_BOTH));

        /*
         * Minarca Status
         */
        // Label
        ft.createLabel(comp, _("Minarca status"), AppFormToolkit.CLASS_BOLD);
        // List
        CList statusItemlist = new CList(comp, SWT.BORDER);
        statusItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        // Last backup
        lastruntimeItem = new CListItem(statusItemlist, _("Last Backup"));
        lastruntimeItem.setValue(StringUtils.EMPTY);
        stopStartButton = lastruntimeItem.createButton(_("Start backup"));
        stopStartButton.setEnabled(false);
        stopStartButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleStopStartBackup();
            }
        });
        new Label(statusItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);
        // Connectivity status.
        statusItem = new CListItem(statusItemlist, _("Connectivity status"));
        statusItem.setValue(StringUtils.EMPTY);
        // statusItem.setTitleHelpText(_("{0} @ {1} / {2}", API.instance().config().getUsername(),
        // API.instance().config().getRemotehost(),
        // API.instance().config().getRepositoryName()));
        unlinkButton = statusItem.createButton(_("Unlink"));
        unlinkButton.setToolTipText(_("Unlink you system from Minarca"));
        unlinkButton.setEnabled(false);
        unlinkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleUnlinkComputer();
            }
        });

        /*
         * Schedule
         */
        // Label
        Label scheduleLabel = new Label(comp, SWT.NONE);
        scheduleLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        scheduleLabel.setText(_("Schedule"));
        // Frequency
        CList scheduleItemlist = new CList(comp, SWT.BORDER);
        scheduleItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, false, false));
        CListItem scheduleItem = new CListItem(scheduleItemlist, _("Define the backup frequency"));
        scheduleCombo = new ComboViewer(scheduleItem.createCombo(SWT.READ_ONLY));
        scheduleCombo.setLabelProvider(new LabelProvider() {
            @Override
            public String getText(Object element) {
                switch ((Schedule) element) {
                case HOURLY:
                    return _("Hourly");
                case DAILY:
                    return _("Daily");
                case WEEKLY:
                    return _("Weekly");
                case MONTHLY:
                    return _("Monthly");
                }
                return element.toString();
            }

        });
        scheduleCombo.add(new Schedule[] { Schedule.HOURLY, Schedule.DAILY, Schedule.WEEKLY, Schedule.MONTHLY });
        Point size = scheduleCombo.getControl().computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
        ((GridData) scheduleCombo.getControl().getLayoutData()).widthHint = size.x;
        ((GridData) scheduleCombo.getControl().getLayoutData()).heightHint = size.y;
        scheduleCombo.addSelectionChangedListener(new ISelectionChangedListener() {
            @Override
            public void selectionChanged(SelectionChangedEvent event) {
                handleSchedule(event);
            }
        });
        // Update schedule
        scheduleCombo.setSelection(new StructuredSelection(API.instance().config().getSchedule()));

        // TODO Pause

        /*
         * Backup
         */
        // Create label.
        Label backupLabel = new Label(comp, SWT.NONE);
        backupLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        backupLabel.setText(_("Backup"));
        // List
        CList backupItemlist = new CList(comp, SWT.BORDER);
        backupItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        // Browse
        CListItem browseItem = new CListItem(backupItemlist, _("Go to Minarca website"));
        Button browseButton = browseItem.createButton(_("Browse my backup"));
        browseButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleBrowse();
            }
        });
        new Label(backupItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);
        /*
         * Selective backup
         */
        CListItem selectiveBackupItem = new CListItem(backupItemlist, _("Selective backup"));
        selectiveBackupItem.setTitleHelpText(_("Allow you to select files and folders to backup."));
        Button selectiveButton = selectiveBackupItem.createButton(_("Select my files"));
        selectiveButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleSelectiveBackup();
            }
        });

        // Add dispose listener
        comp.addDisposeListener(new DisposeListener() {
            @Override
            public void widgetDisposed(DisposeEvent arg0) {
                handleDispose();
            }
        });

        // Asynchronously update the UI.
        checkBackupStatus();
        checkConnectivityStatus();

        return comp;
    }

    /**
     * Return a fixed dialog size.
     */
    @Override
    protected Point getInitialSize() {
        // We want an airy interface.
        Point size = getShell().computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
        return getShell().computeSize((int) (size.y * 1.5), SWT.DEFAULT, true);
    }

    /**
     * Return warning background color for CListItem.
     * 
     * @return
     */
    protected Color getWarnBackground() {
        if (JFaceResources.getColorRegistry().hasValueFor(WARN_BACKGROUNG)) {
            return JFaceResources.getColorRegistry().get(WARN_BACKGROUNG);
        }
        RGB rgb = FormColors.blend(new RGB(255, 102, 0), Display.getDefault().getSystemColor(SWT.COLOR_LIST_BACKGROUND).getRGB(), 15);
        JFaceResources.getColorRegistry().put(WARN_BACKGROUNG, rgb);
        return JFaceResources.getColorRegistry().get(WARN_BACKGROUNG);
    }

    /**
     * Called when the user click the button to browse his backup data.
     */
    protected void handleBrowse() {
        // Simply open the URL into the default browser.
        Program.launch(API.instance().config().getRemoteUrl());
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

    protected void handlePauseBackup() {
        // TODO Auto-generated method stub
    }

    /**
     * Called when user change the schedule.
     * 
     * @param event
     *            the selection event
     */
    protected void handleSchedule(SelectionChangedEvent event) {
        Schedule schedule = (Schedule) ((StructuredSelection) event.getSelection()).getFirstElement();
        try {
            API.instance().config().setSchedule(schedule, true);
        } catch (APIException e) {
            DetailMessageDialog.openError(
                    this.getShell(),
                    Display.getAppName(),
                    _("Can't change backup schedule!"),
                    _("Fail to reschedule the backup task."),
                    e);
        }

    }

    /**
     * Called when the user click on the Selective backup button.
     */
    protected void handleSelectiveBackup() {
        SelectiveDialog dlg = new SelectiveDialog(getShell());
        dlg.setPatterns(API.instance().config().getGlobPatterns());
        // Open dialog and check return code.
        if (dlg.open() != Dialog.OK) {
            // Cancel by user.
            return;
        }
        try {
            API.instance().config().setGlobPatterns(dlg.getPatterns(), true);
        } catch (APIException e) {
            LOGGER.error("error updating selective backup configuration", e);
            DetailMessageDialog.openError(
                    this.getShell(),
                    Display.getAppName(),
                    _("Error updating selective backup configuration"),
                    _("Can't change the configuration for unknown reason. If the problem persists, try re-installing Minarca."));
        }

    }

    /**
     * Start backup now.
     */
    protected void handleStopStartBackup() {
        // Check if backup is running
        boolean running = API.instance().status().getLastResult().equals(LastResult.RUNNING);

        if (running) {
            DetailMessageDialog dlg = DetailMessageDialog
                    .openYesNoQuestion(
                            this.getShell(),
                            Display.getAppName(),
                            _("Are you sure you want to stop the current running backup?"),
                            _("You are about to stop the running backup. Interupting the backup may temporarily disrupt data restore. Are you sure you want to continue?"),
                            (String) null);
            if (dlg.getReturnCode() != IDialogConstants.YES_ID) {
                LOGGER.info("stop backup cancel by user");
                return;
            }

            // Remove last date.
            lastruntimeItem.setValue(StringUtils.EMPTY);

            // Stop backup
            try {
                API.instance().stopBackup();
            } catch (APIException e) {
                LOGGER.error("an error occurred while stopping the backup", e);
                DetailMessageDialog.openError(
                        this.getShell(),
                        Display.getAppName(),
                        _("Can't stop running backup!"),
                        _("An error occurred while stopping the backup."));
            }

        } else {
            // Show a confirmation message.
            DetailMessageDialog dlg = DetailMessageDialog
                    .openYesNoQuestion(
                            this.getShell(),
                            Display.getAppName(),
                            _("Do you want to backup your system now?"),
                            _("You are about to backup your system to Minarca. This operation may take some time. While this operation is running you may safely close the Minarca application."),
                            null);
            if (dlg.getReturnCode() != IDialogConstants.YES_ID) {
                LOGGER.info("backup cancel by user");
                return;
            }

            // Remove last date.
            lastruntimeItem.setValue(StringUtils.EMPTY);

            // Start backup
            try {
                API.instance().backup(true, true);
            } catch (Exception e) {
                LOGGER.error("an error occurred while backuping this computer", e);
                DetailMessageDialog.openError(
                        this.getShell(),
                        Display.getAppName(),
                        _("Can't backup this system!"),
                        _("An error occurred while backuping this system."));
            }
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
                _("Are you sure you want to unlink this system from Minarca?"),
                _("You are about to unlink this system from Minarca. This "
                        + "system will no longer backup it self. Previous "
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
            LOGGER.error("an error occurred while unlinking this system", e);
            DetailMessageDialog.openError(this.getShell(), _("Error"), _("Can't unlink this system!"), _("An error occurred while unlinking this system."));
        }

        // Then close this dialog to open the setup dialog.
        close();

    }

    /**
     * Called when user press to help button.
     */
    private void helpPressed() {
        Program.launch(_("http://www.patrikdufresne.com/en/minarca/faq/"));
    }

}
