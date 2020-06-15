/*
 * Copyright (C) 2020 IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.ui.Localized._;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.mutable.MutableInt;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.ProgressIndicator;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.window.DefaultToolTip;
import org.eclipse.jface.window.ToolTip;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.swt.widgets.Text;
import org.eclipse.ui.forms.widgets.Form;
import org.eclipse.ui.forms.widgets.TableWrapData;
import org.eclipse.ui.forms.widgets.TableWrapLayout;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupFailedException;
import com.patrikdufresne.minarca.core.APIException.RepositoryNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.Client;
import com.patrikdufresne.minarca.core.internal.Compat;

/**
 * Dialog used to configure the application the first time the user open it. It's similar to a wizard.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SetupDialog extends Dialog {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SetupDialog.class);

    /**
     * Open this dialog.
     * 
     * @param parentShell
     * @return True if the setup is a success. False if cancel by user.
     */
    public static boolean open(Shell parentShell) {
        SetupDialog dlg = new SetupDialog(parentShell);
        dlg.setBlockOnOpen(true);
        return dlg.open() == Window.OK;
    }

    /**
     * Connection to minarca.
     */
    private Client client;
    /**
     * The composite holding the page.
     */
    private Composite comp;

    private ScheduledExecutorService executor = Executors.newScheduledThreadPool(1);

    /**
     * Form tool kit to provide a webpage style.
     */
    private AppFormToolkit ft;

    private ScheduledFuture validateConnectivityTask;

    /**
     * Default constructor
     * 
     * @param parentShell
     */
    protected SetupDialog(Shell parentShell) {
        super(parentShell);
    }

    @Override
    public boolean close() {
        boolean returnValue = super.close();
        if (returnValue) {
            executor.shutdown();
        }
        return returnValue;
    }

    /**
     * Add a ticlet to the dialog.
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(_("Setup Minarca"));
    }

    /**
     * Replace the default implementation to create a Form
     */
    @Override
    protected Control createContents(Composite parent) {

        this.ft = new AppFormToolkit(parent.getDisplay(), false);

        // Create the Form.
        Form form = ft.createForm(parent);

        // create the top level composite for the dialog
        // Composite composite = new Composite(parent, 0);
        GridLayout layout = new GridLayout();
        layout.marginHeight = 0;
        layout.marginWidth = 0;
        layout.verticalSpacing = 0;
        form.getBody().setLayout(layout);
        form.setLayoutData(new GridData(GridData.FILL_BOTH));
        // create the dialog area and button bar
        dialogArea = createDialogArea(form.getBody());

        return form;
    }

    /**
     * Create the first page.
     */
    @Override
    protected Control createDialogArea(Composite parent) {

        this.comp = ft.createComposite(parent, SWT.BORDER);
        this.comp.setLayoutData(new GridData(GridData.FILL_BOTH));
        TableWrapLayout layout = new TableWrapLayout();
        layout.topMargin = layout.bottomMargin = 5;
        layout.rightMargin = layout.leftMargin = 25;
        this.comp.setLayout(layout);

        // Introduction message
        Label iconLabel = this.ft.createLabel(comp, StringUtils.EMPTY, SWT.NONE);
        iconLabel.setImage(JFaceResources.getImageRegistry().get(Images.MINARCA_128_PNG));
        iconLabel.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        Label title = this.ft.createLabel(comp, _("Tell Minarca where to backup your data"), AppFormToolkit.CLASS_H3);
        title.setLayoutData(new TableWrapData(TableWrapData.CENTER));
        this.ft
                .createLabel(
                        comp,
                        _(
                                "To configure Minarca to backup your data, "
                                        + "you must provide the URL of a Minara server. "
                                        + "This information should be provided to you by your system administrator."),
                        SWT.WRAP | SWT.CENTER);

        // Remote server
        this.ft.createLabel(comp, _("Address"), AppFormToolkit.CLASS_BOLD);
        final Text remoteserverText = ft.createText(comp, "", SWT.BORDER);
        remoteserverText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        remoteserverText.setToolTipText(_("Enter the remote server address. Either an IP address and port or a URL. e.g.: http://example.com:8080"));
        remoteserverText.setFocus();
        this.ft.createLabel(comp, _("http[s]://hostname[:port]"), AppFormToolkit.CLASS_SMALL);

        // Username & Password
        this.ft.createLabel(comp, _("Username"), AppFormToolkit.CLASS_BOLD);
        final Text usernameText = ft.createText(comp, "", SWT.BORDER);
        usernameText.setLayoutData(new TableWrapData(TableWrapData.FILL));

        this.ft.createLabel(comp, _("Password"), AppFormToolkit.CLASS_BOLD);
        final Text passwordText = ft.createText(comp, "", SWT.PASSWORD | SWT.BORDER);
        passwordText.setLayoutData(new TableWrapData(TableWrapData.FILL));

        final Label connectError = this.ft.createLabel(comp, StringUtils.EMPTY);
        connectError.setLayoutData(new TableWrapData(TableWrapData.FILL));
        final DefaultToolTip connectErrorToolTip = new DefaultToolTip(connectError, ToolTip.NO_RECREATE, false);

        // Computer name
        this.ft.createLabel(comp, _("Repository name"), AppFormToolkit.CLASS_BOLD);
        final Text computerNameText = ft.createText(comp, "", SWT.BORDER);
        computerNameText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        computerNameText.setText(Compat.COMPUTER_NAME);
        this.ft
                .createLabel(
                        comp,
                        _(
                                "You must provide a unique name to identify this computer in Minarca. "
                                        + "Please, provide a friendly name. By default, the computer's name is used. "
                                        + "This value cannot be changed."),
                        SWT.WRAP,
                        AppFormToolkit.CLASS_SMALL);

        Label alertLabel = this.ft.createLabel(comp, StringUtils.EMPTY);
        alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Sign in button
        final Button linkButton = ft.createButton(comp, _("Link"), SWT.PUSH);
        linkButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
        linkButton.setEnabled(false);
        getShell().setDefaultButton(linkButton);

        // Progress bar
        final ProgressIndicator progress = new ProgressIndicator(comp);
        ft.adapt(progress);
        progress.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Enable Sing-In button when all field contains something.
        // Also provide feedback to the user.
        ModifyListener modifyListener = new ModifyListener() {
            @Override
            public void modifyText(ModifyEvent event) {
                // Disable the link button immetiatly when one of the fields is blank.
                final String computerName = computerNameText.getText();
                final String remoteServer = remoteserverText.getText();
                final String username = usernameText.getText();
                final String password = passwordText.getText();
                if (StringUtils.isBlank(computerName) || StringUtils.isBlank(remoteServer) || StringUtils.isBlank(username) || StringUtils.isBlank(password)) {
                    linkButton.setEnabled(false);
                }

                // Enable the Link button if the url, user and password are valid AND if the repo is not empty.
                validateConnectivity(remoteserverText.getText(), usernameText.getText(), passwordText.getText(), (APIException e) -> {
                    Display.getDefault().asyncExec(new Runnable() {
                        @Override
                        public void run() {
                            if (e != null) {
                                connectError.setText(e.getMessage());
                                StringWriter buf = new StringWriter();
                                e.printStackTrace(new PrintWriter(buf));
                                connectErrorToolTip.setText(buf.toString());
                                connectErrorToolTip.activate();
                                ft.setSkinClass(connectError, AppFormToolkit.CLASS_SMALL, AppFormToolkit.CLASS_ERROR);
                                linkButton.setEnabled(false);
                            } else {
                                connectError.setText(_("Connected"));
                                connectErrorToolTip.setText(null);
                                connectErrorToolTip.deactivate();
                                ft.setSkinClass(connectError, AppFormToolkit.CLASS_SMALL, AppFormToolkit.CLASS_SUCESS);
                                linkButton.setEnabled(StringUtils.isNotBlank(computerName));
                            }
                        }
                    });
                });
            }
        };
        remoteserverText.addModifyListener(modifyListener);
        usernameText.addModifyListener(modifyListener);
        passwordText.addModifyListener(modifyListener);
        computerNameText.addModifyListener(modifyListener);

        // Add event binding.
        linkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {

                // What a mess. Blame Java.
                final String remoteServer = remoteserverText.getText();
                final String username = usernameText.getText();
                final String password = passwordText.getText();
                final String computerName = computerNameText.getText();
                linkButton.setEnabled(false);
                progress.beginAnimatedTask();

                // Start the processing.
                link(remoteServer, username, password, computerName, false, (APIException e1) -> {
                    Display.getDefault().asyncExec(new Runnable() {
                        @Override
                        public void run() {
                            linkButton.setEnabled(true);
                            progress.done();
                            if (e1 == null) {
                                SetupDialog.this.close();
                                return;
                            }
                            // Show the exception.
                            progress.showError();
                            String message = e1.getLocalizedMessage();
                            String details = e1 instanceof InitialBackupFailedException ? ((InitialBackupFailedException) e1).getDetails() : null;
                            DetailMessageDialog
                                    .openWarning(
                                            getShell(),
                                            Display.getAppName(),
                                            _("A problem happend during the linking process to Minarca server!"),
                                            message,
                                            details);

                        }
                    });
                });
            }
        });

        return comp;

    }

    /**
     * Return a fixed dialog size.
     */
    @Override
    protected Point getInitialSize() {
        Point size = getShell().computeSize(681, SWT.DEFAULT, true);
        size.y += 50;
        return size;
    }

    /**
     * Called to handle computer registration.
     * <p>
     * This step is used to exchange the SSH keys.
     * 
     * @param remoteserver
     *            the remote server address.
     * @param username
     *            the username for authentication
     * @param password
     *            the password for authentication.
     * @param name
     *            the computer name.
     * @return an error message or null if OK.
     */
    protected void link(String remoteserver, String username, String password, String name, boolean force, Consumer<APIException> callback) {
        this.executor.schedule(new Runnable() {

            @Override
            public void run() {
                try {
                    client = API.instance().connect(remoteserver, username, password);
                } catch (APIException e) {
                    callback.accept(e);
                    return;
                }

                // Little validation before
                LOGGER.info("link computer {}", name);
                try {
                    try {
                        API.instance().link(name, client, force);
                        callback.accept(null);
                    } catch (RepositoryNameAlreadyInUseException e) {
                        final MutableInt returnCode = new MutableInt();
                        Display.getDefault().syncExec(() -> {
                            int r = DetailMessageDialog
                                    .openYesNoQuestion(
                                            getShell(),
                                            Display.getAppName(),
                                            _("Repository name {0} already exists ! Do you want to keep the given repository name ?", name),
                                            _(
                                                    "The given repository name is already exists in Mianrca. "
                                                            + "You may safely keep this repository name if the name is "
                                                            + "not used by another computer linked to Minarca."),
                                            null)
                                    .getReturnCode();
                            returnCode.setValue(r);
                        });
                        if (returnCode.intValue() == IDialogConstants.YES_ID) {
                            // Force usage of the computer name
                            API.instance().link(name, client, true);
                            callback.accept(null);
                        } else {
                            callback.accept(e);
                        }
                    }
                } catch (InterruptedException e) {
                    // Nothing to do.
                    LOGGER.error("fail to link", e);
                    callback.accept(new APIException(_("Link process interrupted")));
                } catch (IllegalArgumentException e) {
                    LOGGER.error("fail to link", e);
                    callback.accept(new APIException(e.getMessage()));
                } catch (APIException e) {
                    LOGGER.error("fail to link", e);
                    callback.accept(e);
                } catch (Exception e) {
                    LOGGER.error("fail to link", e);
                    callback
                            .accept(
                                    new APIException(
                                            _(
                                                    "Unexpected error happen during the linking process with the server. Verify connectivity with the server and try again later.")));
                }
            }

        }, 1, TimeUnit.MILLISECONDS);
    }

    /**
     * Called to validate the connectivity with the given parameter.
     * <p>
     * This function will run the validation. in a background task in 250ms unless the function is called again.
     */
    public void validateConnectivity(final String remoteserver, final String username, final String password, Consumer<APIException> callback) {
        if (validateConnectivityTask != null) {
            validateConnectivityTask.cancel(false);
        }
        if (StringUtils.isBlank(remoteserver) || StringUtils.isBlank(username) || StringUtils.isBlank(password)) {
            return;
        }
        validateConnectivityTask = executor.schedule(new Runnable() {
            @Override
            public void run() {
                try {
                    LOGGER.error("validating connectivity to {} at {}", username, remoteserver);
                    API.instance().connect(remoteserver, username, password);
                    callback.accept(null);
                } catch (APIException e) {
                    LOGGER.error("fail to validate connectivity", e);
                    callback.accept(e);
                } catch (Exception e3) {
                    LOGGER.error("fail to validate connectivity", e3);
                    callback.accept(new APIException(_("Unexpected error occured"), e3));
                }
            }
        }, 250, TimeUnit.MILLISECONDS);
    }

}
