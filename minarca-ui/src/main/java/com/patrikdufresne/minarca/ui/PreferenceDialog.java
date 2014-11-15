package com.patrikdufresne.minarca.ui;

import org.eclipse.jface.dialogs.TitleAreaDialog;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Shell;

/**
 * This is the main windows of the application used to configure the backup.
 * 
 * @author ikus060
 * 
 */
public class PreferenceDialog extends TitleAreaDialog {

    public PreferenceDialog() {
        super((Shell) null);
    }

    protected Control createDialogArea(Composite parent) {
        return super.createDialogArea(parent);
    }

}
