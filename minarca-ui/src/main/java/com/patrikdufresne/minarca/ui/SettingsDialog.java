/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.text.DateFormat;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.resource.JFaceResources;
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

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.internal.Scheduler.TaskInfo;
import com.patrikdufresne.minarca.ui.fontawesome.FontAwesome;
import com.patrikdufresne.switchbutton.SwitchButton;

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
        TaskInfo info = null;
        try {
            info = API.instance().getScheduleTaskInfo();
        } catch (APIException e) {
            LOGGER.warn("fail to get backup info", e);
        }
        // Update UI
        final TaskInfo fInfo = info;
        Display.getDefault().asyncExec(new Runnable() {
            @Override
            public void run() {
                if (!lastruntimeItem.isDisposed()) {
                    if (fInfo != null && fInfo.isRunning()) {
                        lastruntimeItem.setValue(_("Running..."));
                        stopStartButton.setEnabled(true);
                        stopStartButton.setText(_("Stop"));
                    } else if (fInfo != null && fInfo.getLastRun() != null) {
                        String text = DateFormat.getDateTimeInstance().format(fInfo.getLastRun());
                        lastruntimeItem.setValue(text);
                        stopStartButton.setEnabled(true);
                        stopStartButton.setText(_("Start"));
                    } else {
                        lastruntimeItem.setValue(_("Unknown"));
                        stopStartButton.setEnabled(false);
                    }
                    if (fInfo != null && fInfo.getLastResult() != null) {
                        if (fInfo.getLastResult().intValue() == 0) {
                            lastruntimeItem.setValueHelpText(_("Successful"));
                        } else {
                            lastruntimeItem.setValueHelpText(_("Failed"));
                        }
                    } else {
                        lastruntimeItem.setValueHelpText(null);
                    }
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
            helpButton.setText(FontAwesome.QUESTION);
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
            aboutButton.setText(FontAwesome.INFO);
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
        Label accountSettingsLabel = new Label(comp, SWT.NONE);
        accountSettingsLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        accountSettingsLabel.setText(_("Account settings"));

        // Create list
        CList accountItemlist = new CList(comp, SWT.BORDER);
        accountItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, false, false));

        // Create status
        statusItem = new CListItem(accountItemlist, _("Status"));
        statusItem.setValue(Dialog.ELLIPSIS);
        statusItem.setValueHelpText(_("As {0} @ {1}", API.instance().getUsername(), API.instance().getComputerName()));
        unlinkButton = statusItem.createButton(_("Unlink..."));
        unlinkButton.setToolTipText(_("Unlink you computer from minarca."));
        unlinkButton.setEnabled(false);
        unlinkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleUnlinkComputer();
            }
        });

        // Separator.
        new Label(accountItemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create fingerprint
        CListItem fingerprintItem = new CListItem(accountItemlist, _("Fingerprint"));
        fingerprintItem.setValue(API.instance().getIdentityFingerPrint());
        fingerprintItem.setValueHelpText(_("Use by your computer to identify it self."));

        // Create label.
        Label backupSettingsLabel = new Label(comp, SWT.NONE);
        backupSettingsLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        backupSettingsLabel.setText(_("Backup settings"));

        // Create list
        CList backupItemlist = new CList(comp, SWT.BORDER);
        backupItemlist.setLayoutData(new GridData(SWT.FILL, SWT.FILL, false, false));

        // Create selective backup
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

        // Create Last run time
        lastruntimeItem = new CListItem(backupItemlist, _("Last run time"));
        lastruntimeItem.setValue(_("..."));
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
        // Sets fixed window size.
        // if (SystemUtils.IS_OS_LINUX) {
        // return new Point(450, 550);
        // }
        // return new Point(425, 500);
        return super.getInitialSize();
    }

    /**
     * Return warning background color for CListItem.
     * 
     * @return
     */
    protected Color getWarnBackground() {
        if (!JFaceResources.getColorRegistry().hasValueFor(WARN_BACKGROUNG)) {
            return JFaceResources.getColorRegistry().get(WARN_BACKGROUNG);
        }
        RGB rgb = FormColors.blend(new RGB(255, 0, 0), Display.getDefault().getSystemColor(SWT.COLOR_LIST_SELECTION).getRGB(), 15);
        JFaceResources.getColorRegistry().put(WARN_BACKGROUNG, rgb);
        return JFaceResources.getColorRegistry().get(WARN_BACKGROUNG);
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
        dlg.setIncludes(API.instance().getIncludes());
        dlg.setExcludes(API.instance().getExcludes());
        // Open dialog and check return code.
        if (dlg.open() != Dialog.OK) {
            // Cancel by user.
            return;
        }
        try {
            API.instance().setIncludes(dlg.getIncludes());
            API.instance().setExcludes(dlg.getExcludes());
        } catch (APIException e) {
            DetailMessageDialog.openError(
                    this.getShell(),
                    _("Error"),
                    _("Error updating selective backup configuration"),
                    _("Can't change the configuration for unknown reason. If the problem persists, try re-installing minarca."));
        }

    }

    /**
     * Start backup now.
     */
    protected void handleStopStartBackup() {
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
     * Called when user press to help button.
     */
    private void helpPressed() {
        // TODO: Change this url to point to How-to
        Program.launch("https://www.minarca.net/help/");
    }

}
