package com.patrikdufresne.minarca.ui;

import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.ui.forms.FormColors;

public class CListTest {

    public static void main(String[] args) {

        final Display display = new Display();
        final Shell shell = new Shell(display);
        shell.setText("SwitchButton Snippet");
        shell.setLayout(new GridLayout(1, false));

        // Create hot zone.

        CList itemlist = new CList(shell, SWT.NONE);

        // Create item
        CListItem item1 = new CListItem(itemlist, "Line with help text");
        item1.setTitleHelpText("Help text");
        item1.setValue("Linked");

        Label sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item2 = new CListItem(itemlist, "With buton");
        item2.setValue("Value");
        item2.setValueHelpText("Value help text");
        Button unlink = item2.createButton("Unlink...");

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);
        // sep.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));

        // Create item
        CListItem item3 = new CListItem(itemlist, "Fingerprint");
        item3.setValue("2f:1f:fe:7e:d6:a9:30:ac:7a:a2:33:78:f6:09:fa:74");

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item4 = new CListItem(itemlist, "Empty line");

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item5 = new CListItem(itemlist, "With alot of help");
        item5.setTitleHelpText("Help text");
        item5.setValue("Value");
        item5.setValueHelpText("A very long help text to be displayed.");

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item6 = new CListItem(itemlist, "With button");
        item6.createButton("Start");
        item6.setValue("Value");

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item7 = new CListItem(itemlist, "Disabled");
        item7.setEnabled(false);
        item7.createSwitchButton();
        item7.createButton("Start");
        item7.setValue("Value");

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item8 = new CListItem(itemlist, "Switch button");
        item8.createSwitchButton();
        item8.createButtonConfig();

        // Seperator.
        sep = new Label(itemlist, SWT.SEPARATOR | SWT.HORIZONTAL);

        // Create item
        CListItem item9 = new CListItem(itemlist, "With background color");
        item9.createSwitchButton();
        Color red = new Color(Display.getDefault(), FormColors.blend(Display.getDefault().getSystemColor(SWT.COLOR_RED).getRGB(), item9
                .getBackground()
                .getRGB(), 15));
        item9.setValue("Failed");
        item9.setValueHelpText("Unknown reason");
        item9.setBackground(red);

        // Create item
        CListItem item10 = new CListItem(itemlist, "Status");
        Color green = new Color(Display.getDefault(), FormColors.blend(Display.getDefault().getSystemColor(SWT.COLOR_GREEN).getRGB(), item10
                .getBackground()
                .getRGB(), 15));
        item10.setValue("Linked");
        item10.setValueHelpText("Tested a minute ago");
        item10.setBackground(green);
        item10.createButton("Unlink...");

        // Create item
        CListItem item11 = new CListItem(itemlist, "My Autocad files");
        item11.setTitleHelpText("/home/ikus060/my files/autocad files");
        item11.createSwitchButton();
        item11.createButtonDelete();

        shell.pack();
        shell.open();

        while (!shell.isDisposed()) {
            if (!display.readAndDispatch()) {
                display.sleep();
            }
        }
        display.dispose();
    }

}
