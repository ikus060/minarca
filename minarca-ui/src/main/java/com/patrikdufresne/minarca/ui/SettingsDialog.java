/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.IOException;
import java.text.DateFormat;
import java.util.Date;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

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
import com.patrikdufresne.minarca.core.internal.Compat;

/**
 * This is the main windows of the application used to configure the backup.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SettingsDialog extends Dialog {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SettingsDialog.class);

    /**
     * Symbolic name for warning background color.
     */
    private static final String WARN_BACKGROUNG = "WARN_BACKGROUNG";

    /**
     * Button id for About button.
     */
    private int ABOUT_ID = IDialogConstants.CLIENT_ID;

    /**
     * Label for about button.
     */
    private String ABOUT_LABEL = _("About");

    /**
     * Create an executor service to asynchronously update the UI.
     */
    private ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();

    private CListItem lastruntimeItem;

    private CListItem statusItem;

    private Button stopStartButton;

    private Button unlinkButton;

    private ComboViewer scheduleCombo;

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
     * Asynchronously check backup info.
     * 
     * @param backupinfo
     */
    private void asynchCheckBackupInfo() {
        executor.scheduleAtFixedRate(new Runnable() {
            @Override
            public void run() {
                // Then check link.
                checkBackupInfo();
            }
        }, 1000, 15000, TimeUnit.MILLISECONDS);
    }

    /**
     * Asynchronously check link with minarca.
     * 
     * @param formtext
     */
    private void asynchCheckLink() {
        executor.schedule(new Runnable() {
            @Override
            public void run() {
                // Then check link.
                checkLink();
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
        } else if (IDialogConstants.HELP_ID == buttonId) {
            helpPressed();
        } else if (ABOUT_ID == buttonId) {
            aboutPressed();
        } else {
            super.buttonPressed(buttonId);
        }
    }

    /**
     * Check backup info and update the UI accordingly.
     * 
     * @param backupinfo
     */
    private void checkBackupInfo() {
        // Get backup info.
        final LastResult lastResult = API.instance().getLastResult();
        final Date lastDate = API.instance().getLastResultDate();
        Schedule temp = null;
        try {
            temp = API.instance().getSchedule();
        } catch (APIException e) {
            // Do nothing.
        }
        final Schedule schedule = temp;

        // Update UI
        Display.getDefault().asyncExec(new Runnable() {
            @Override
            public void run() {
                if (lastruntimeItem.isDisposed()) {
                    return;
                }

                // Update value with last date.
                if (lastDate == null || LastResult.RUNNING.equals(lastResult) || LastResult.HAS_NOT_RUN.equals(lastResult)) {
                    lastruntimeItem.setValueHelpText(null);
                } else {
                    String text = DateFormat.getDateTimeInstance().format(lastDate);
                    lastruntimeItem.setValueHelpText(text);
                }

                // Update label button according to task state.
                if (LastResult.UNKNOWN.equals(lastResult)) {
                    stopStartButton.setEnabled(false);
                } else {
                    stopStartButton.setEnabled(true);
                    stopStartButton.setText(LastResult.RUNNING.equals(lastResult) ? _("Stop") : _("Start"));
                }

                // Update help text with Success or Failure
                switch (lastResult) {
                case RUNNING:
                    lastruntimeItem.setValue(_("Running..."));
                    break;
                case SUCCESS:
                    lastruntimeItem.setValue(_("Successful"));
                    break;
                case FAILURE:
                    lastruntimeItem.setValue(_("Failed"));
                    break;
                case HAS_NOT_RUN:
                    lastruntimeItem.setValue(_("Never"));
                    break;
                case STALE:
                    lastruntimeItem.setValue(_("Stale"));
                    break;
                default:
                    lastruntimeItem.setValue(_("Unknown"));
                    break;
                }

                // Update schedule
                if (schedule != null) {
                    scheduleCombo.setSelection(new StructuredSelection(schedule));
                    scheduleCombo.getControl().setEnabled(true);
                } else {
                    scheduleCombo.getControl().setEnabled(false);
                }

            }
        });
    }

    /**
     * Asynchronously check link with minarca.
     * 
     * @param textlink
     */
    private void checkLink() {
        // Test the connectivity with minarca using test.
        String text;
        boolean linked;
        try {
            API.instance().testServer();
            linked = true;
            text = _("Linked");
        } catch (APIException e) {
            // TODO: Complete this to provide the right status: can't connect, refused, etc.
            linked = false;
            text = _("Unknown");

        }
        final String fText = text;
        final boolean fLinked = linked;
        Display.getDefault().asyncExec(new Runnable() {
            @Override
            public void run() {
                // Update the value of status item
                if (!statusItem.isDisposed()) {
                    statusItem.setValue(fText);
                }
                // Update the colour of the status.
                if (!fLinked) {
                    statusItem.setBackground(getWarnBackground());
                }
                // Update button enabled state.
                unlinkButton.setEnabled(true);
            }
        });
    }

    /**
     * Sets dialog title
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(_("Minarca Settings"));
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

        Composite comp = (Composite) super.createDialogArea(parent);

        // Create label.
        Label browseLabel = new Label(comp, SWT.NONE);
        browseLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        browseLabel.setText(_("Your data"));

        // Create list
        CList browseItemlist = new CList(comp, SWT.BORDER);
        browseItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, false, false));

        /*
         * Browse data
         */
        CListItem browseItem = new CListItem(browseItemlist, _("Go to Minarca website"));
        browseItem.setTitleHelpText(_("Allows you to browse your backup and restore files."));
        Button browseButton = browseItem.createButtonConfig();
        browseButton.setText("");
        browseButton.setImage(JFaceResources.getImageRegistry().get(Images.MINARCA_16_PNG));
        browseButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleBrowse();
            }
        });

        // Create label.
        Label accountSettingsLabel = new Label(comp, SWT.NONE);
        accountSettingsLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        accountSettingsLabel.setText(_("Account settings"));

        // Create list
        CList accountItemlist = new CList(comp, SWT.BORDER);
        accountItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, false, false));

        /*
         * Status
         */
        statusItem = new CListItem(accountItemlist, _("Status"));
        statusItem.setValue(Dialog.ELLIPSIS);
        statusItem.setValueHelpText(_("As {0} @ {1}", API.instance().getUsername(), API.instance().getComputerName()));
        unlinkButton = statusItem.createButton(_("Unlink..."));
        unlinkButton.setToolTipText(_("Unlink you computer from Minarca."));
        unlinkButton.setEnabled(false);
        unlinkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleUnlinkComputer();
            }
        });

        // Separator.
        new Label(accountItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        /*
         * Fingerprint
         */
        CListItem fingerprintItem = new CListItem(accountItemlist, _("Fingerprint"));
        fingerprintItem.setValue(API.instance().getIdentityFingerPrint());
        fingerprintItem.setValueHelpText(_("Use by your computer to identify itself."));

        // Create label.
        Label backupSettingsLabel = new Label(comp, SWT.NONE);
        backupSettingsLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        backupSettingsLabel.setText(_("Backup settings"));

        // Create list
        CList backupItemlist = new CList(comp, SWT.BORDER);
        backupItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, false, false));

        /*
         * Selective backup
         */
        CListItem selectiveBackupItem = new CListItem(backupItemlist, _("Selective backup"));
        selectiveBackupItem.setTitleHelpText(_("Allow you to select files and folders to backup."));
        Button selectiveButton = selectiveBackupItem.createButtonConfig();
        selectiveButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleSelectiveBackup();
            }
        });

        // Separator.
        // new Label(backupItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create pause
        // CListItem pauseItem = new CListItem(backupItemlist, _("Pause backup"));
        // pauseItem.setTitleHelpText(_("Used to temporarily stop backup."));
        // SwitchButton pauseButton = pauseItem.createSwitchButton();
        // pauseButton.addSelectionListener(new SelectionAdapter() {
        // @Override
        // public void widgetSelected(SelectionEvent e) {
        // handlePauseBackup();
        // }
        // });

        // Separator.
        new Label(backupItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        /*
         * Schedule
         */
        CListItem scheduleItem = new CListItem(backupItemlist, _("Schedule"));
        scheduleItem.setTitleHelpText(_("Define the backup frequency."));
        scheduleCombo = new ComboViewer(scheduleItem.createCombo(SWT.READ_ONLY));
        scheduleCombo.getControl().setEnabled(false);
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
                case UNKNOWN:
                    return _("Unknown");
                }
                return element.toString();
            }

        });
        scheduleCombo.add(new Schedule[] { Schedule.HOURLY, Schedule.DAILY, Schedule.WEEKLY, Schedule.MONTHLY, Schedule.UNKNOWN });
        Point size = scheduleCombo.getControl().computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
        ((GridData) scheduleCombo.getControl().getLayoutData()).widthHint = size.x;
        ((GridData) scheduleCombo.getControl().getLayoutData()).heightHint = size.y;
        scheduleCombo.addSelectionChangedListener(new ISelectionChangedListener() {
            @Override
            public void selectionChanged(SelectionChangedEvent event) {
                handleSchedule(event);
            }
        });
        Button scheduleButton = scheduleItem.createButtonConfig();
        scheduleButton.setToolTipText(_("Advance scheduler configuration."));
        scheduleButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleScheduleAdvance();
            }
        });

        // Separator.
        new Label(backupItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        /*
         * Last run time & Start / Stop
         */
        lastruntimeItem = new CListItem(backupItemlist, _("Last run time"));
        lastruntimeItem.setValue(Dialog.ELLIPSIS);
        stopStartButton = lastruntimeItem.createButton(_("Start"));
        stopStartButton.setEnabled(false);
        stopStartButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleStopStartBackup();
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
        asynchCheckBackupInfo();
        asynchCheckLink();

        return comp;
    }

    /**
     * Define dialog size.
     */
    @Override
    protected Point getInitialSize() {
        return super.getInitialSize();
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
        Program.launch(API.instance().getBrowseUrl());
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
     * Called when the user click on the Selective backup button.
     */
    protected void handleSelectiveBackup() {
        SelectiveDialog dlg = new SelectiveDialog(getShell());
        dlg.setPatterns(API.instance().getGlobPatterns());
        // Open dialog and check return code.
        if (dlg.open() != Dialog.OK) {
            // Cancel by user.
            return;
        }
        try {
            API.instance().setGlobPatterns(dlg.getPatterns());
        } catch (APIException e) {
            DetailMessageDialog.openError(
                    this.getShell(),
                    _("Error"),
                    _("Error updating selective backup configuration"),
                    _("Can't change the configuration for unknown reason. If the problem persists, try re-installing Minarca."));
        }

    }

    /**
     * Start backup now.
     */
    protected void handleStopStartBackup() {
        // Check if backup is running
        boolean running = API.instance().getLastResult().equals(LastResult.RUNNING);

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
            lastruntimeItem.setValue(Dialog.ELLIPSIS);
            lastruntimeItem.setValueHelpText(Dialog.ELLIPSIS);

            // Stop backup
            try {
                API.instance().stopBackup();
            } catch (APIException e) {
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
            lastruntimeItem.setValue(Dialog.ELLIPSIS);
            lastruntimeItem.setValueHelpText(Dialog.ELLIPSIS);

            // Start backup
            try {
                API.instance().runBackup();
            } catch (APIException e) {
                DetailMessageDialog.openError(
                        this.getShell(),
                        Display.getAppName(),
                        _("Can't backup this computer!"),
                        _("An error occurred while backuping this computer."));
            }
        }

    }

    /**
     * Called when user change the schedule.
     * 
     * @param event
     *            the selection event
     */
    protected void handleSchedule(SelectionChangedEvent event) {
        Schedule schedule = (Schedule) ((StructuredSelection) event.getSelection()).getFirstElement();
        if (Schedule.UNKNOWN.equals(schedule)) {
            // Do nothing.
            return;
        }
        // Check if the schedule type is different.
        try {
            Schedule current = API.instance().getSchedule();
            if (schedule.equals(current)) {
                // Nothing to do.
                return;
            }
        } catch (APIException e) {
            DetailMessageDialog.openError(
                    this.getShell(),
                    Display.getAppName(),
                    _("Can't change backup schedule!"),
                    _("Fail to retrieve current backup schedule."),
                    e);
        }

        try {
            API.instance().setSchedule(schedule);
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
     * Called when the user click on advance button config for scheduler. This action open the task scheduler.
     */
    protected void handleScheduleAdvance() {

        // Prompt the user.
        DetailMessageDialog dlg = DetailMessageDialog.openOkCancelConfirm(
                getShell(),
                Display.getAppName(),
                _("This action will open Windows Task Scheduler."),
                _("If you want more control over the backup schedule, you need to "
                        + "manually edit the Minarca backup task in Windows Task Scheduler. "
                        + "If you don't know what you are doing, you should cancel the"
                        + "operation to avoid breaking the schedule."),
                null);
        if (dlg.getReturnCode() != IDialogConstants.OK_ID) {
            return;
        }

        // Open Task Scheduler (work in XP to 10)
        File control = Compat.searchFile("control.exe", new String[0]);
        if (control != null) {
            try {
                Runtime.getRuntime().exec(new String[] { control.toString(), "schedtasks" });
            } catch (IOException e) {
                DetailMessageDialog.openError(
                        this.getShell(),
                        Display.getAppName(),
                        _("Can't open Windows Task Scheduler!"),
                        _("An error occurred when trying to open Windows Task Scheduler."),
                        e);
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
                _("Are you sure you want to unlink this computer from Minarca?"),
                _("You are about to unlink this computer from Minarca. This "
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
     * Called when user press to help button.
     */
    private void helpPressed() {
        Program.launch(_("http://www.patrikdufresne.com/en/minarca/help/"));
    }

}
