package com.patrikdufresne.minarca.ui;

import org.apache.commons.lang3.SystemUtils;
import org.eclipse.jface.layout.GridLayoutFactory;
import org.eclipse.jface.layout.PixelConverter;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.DisposeEvent;
import org.eclipse.swt.events.DisposeListener;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.graphics.FontData;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Event;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Layout;
import org.eclipse.swt.widgets.Listener;
import org.eclipse.swt.widgets.Text;

import com.patrikdufresne.minarca.ui.fontawesome.FontAwesome;
import com.patrikdufresne.switchbutton.SwitchButton;

/**
 * Create a new item (used for settings).
 * 
 * @author Patrik Dufresne
 * 
 */
public class CListItem extends Composite {

    private static final int HORIZONTAL_MARGIN = 8;

    // Change the top - bottom margin according to OS.
    private static final int VERTICAL_MARGIN = SystemUtils.IS_OS_WINDOWS ? 6 : 2;

    /**
     * Blends two primary color components based on the provided ratio.
     * 
     * @param v1
     *            first component
     * @param v2
     *            second component
     * @param ratio
     *            percentage of the first component in the blend
     * @return the blended color component
     */
    private static int blend(int v1, int v2, int ratio) {
        int b = (ratio * v1 + (100 - ratio) * v2) / 100;
        return Math.min(255, b);
    }

    private static RGB blend(RGB c1, RGB c2, int ratio) {
        int r = blend(c1.red, c2.red, ratio);
        int g = blend(c1.green, c2.green, ratio);
        int b = blend(c1.blue, c2.blue, ratio);
        return new RGB(r, g, b);
    }

    /**
     * Return the font to be used for icons (delete and config button)
     * 
     * @return the font
     */
    private static Font getIconFont(Control control) {
        String fontName = "ICON_FONT_" + control.getClass().getName(); //$NON-NLS-1$
        if (JFaceResources.getFontRegistry().hasValueFor(fontName)) {
            return JFaceResources.getFontRegistry().get(fontName);
        }
        // Get default font
        Font cached = control.getFont();
        control.setFont(null);
        Font defaultFont = control.getFont();
        control.setFont(cached);
        // Get default font size
        FontData[] data = defaultFont.getFontData();
        int size = data[0].getHeight();
        // Use this default size with font awesome
        data = FontAwesome.getFont().getFontData();
        for (FontData d : data) {
            d.setHeight((int) (size * 1.25f));
        }
        // Register the font.
        JFaceResources.getFontRegistry().put(fontName, data);
        return JFaceResources.getFontRegistry().get(fontName);
    }

    /**
     * The background color.
     */
    private Color bg;
    private Color bgOver;
    /** Light color */
    private Color helpTextFg;
    private Composite left;

    private Label leftTitleHelpLabel;

    /** Widget used to display the principal text. */
    private Label leftTitleLabel;
    /**
     * Lister to know is hover.
     */
    private Listener listener = new Listener() {

        @Override
        public void handleEvent(Event e) {
            Point mouse = getDisplay().map((Control) e.widget, CListItem.this, e.x, e.y);
            if (getClientArea().contains(mouse)) {
                over = true;
                setBackgroundInternal(getOverBackground());
                redraw();
            } else if (!getClientArea().contains(mouse)) {
                over = false;
                setBackgroundInternal(getBackground());
                redraw();
            }
        }
    };
    private boolean over = false;

    private Composite right;

    private Text rightValueHelpText;

    private Text rightValueText;

    /**
     * Create a new instance of list item.
     * 
     * @param parent
     */
    public CListItem(Composite parent) {
        super(parent, SWT.NONE);

        // Set layout (Use pixel converter to get an adaptive margin).
        PixelConverter pc = new PixelConverter(this);
        int marginHeight = pc.convertVerticalDLUsToPixels(VERTICAL_MARGIN);
        int marginWidth = pc.convertHorizontalDLUsToPixels(HORIZONTAL_MARGIN);
        super.setLayout(GridLayoutFactory.swtDefaults().numColumns(2).margins(marginWidth, marginHeight).create());
        // Set background color as white.
        setBackground(Display.getDefault().getSystemColor(SWT.COLOR_LIST_BACKGROUND));
        // Register listeners
        registerlisteners(this);

        // Create Left part.
        left = new Composite(this, SWT.NONE);
        left.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, true, true));
        left.setBackground(getBackground());
        GridLayoutFactory.fillDefaults().spacing(0, 0).applyTo(left);
        registerlisteners(left);

        // Create title text
        leftTitleLabel = new Label(left, SWT.NONE);
        leftTitleLabel.setBackground(getBackground());
        leftTitleLabel.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
        registerlisteners(leftTitleLabel);

        // Right part
        right = new Composite(this, SWT.NONE);
        right.setLayoutData(new GridData(SWT.RIGHT, SWT.CENTER, false, true));
        right.setBackground(getBackground());
        GridLayoutFactory.fillDefaults().spacing(0, 0).applyTo(right);
        registerlisteners(right);

        // Set default layout data
        if (parent.getLayout() instanceof GridLayout) {
            setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        }

        // Add a dispose listener.
        addDisposeListener(new DisposeListener() {
            @Override
            public void widgetDisposed(DisposeEvent e) {
                onDispose();
            }
        });

    }

    /**
     * Create a new instance of list item.
     * 
     * @param parent
     *            the parent.
     * @param title
     *            the title
     */
    public CListItem(Composite parent, String title) {
        this(parent);
        setTitle(title);
    }

    /**
     * Used to increase the number of column in the widget.
     */
    private void addColumn() {
        ((GridLayout) getLayout()).numColumns++;
    }

    /**
     * Create a button in right section. Same as <code>createButton(text, SWT.PUSH)</code>
     * 
     * @param text
     *            the button text
     * 
     * @return the button widget
     */
    public Button createButton(String text) {
        return createButton(text, SWT.PUSH);
    }

    /**
     * Create a button in right section.
     * 
     * @param text
     *            the button text
     * @return the button widget
     */
    public Button createButton(String text, int style) {
        addColumn();
        Button button = new Button(this, style);
        button.setText(text);
        button.setBackground(getBackground());
        button.setLayoutData(new GridData(SWT.RIGHT, SWT.CENTER, false, false));
        button.setEnabled(getEnabled());
        registerlisteners(button);
        return button;
    }

    /**
     * 
     * @return
     */
    public Button createButtonConfig() {
        // Use GEAR icon.
        Button button = createButton("\uf085", SWT.FLAT);
        // Change the font (it's a bigger font).
        button.setFont(getIconFont(button));
        // Set the size of the button to be square
        Point size = button.computeSize(SWT.DEFAULT, SWT.DEFAULT);
        int square = Math.max(size.x, size.y);
        ((GridData) button.getLayoutData()).heightHint = square;
        ((GridData) button.getLayoutData()).widthHint = square;
        return button;
    }

    /**
     * Create a predefine button with appearance to delete the item.
     * 
     * @return
     */
    public Button createButtonDelete() {
        // Use TIME icon (X).
        Button button = createButton(FontAwesome.TIMES, SWT.FLAT);
        // Change the font (it's a bigger font).
        button.setFont(getIconFont(button));
        // Set the size of the button to be square
        Point size = button.computeSize(SWT.DEFAULT, SWT.DEFAULT);
        int square = Math.max(size.x, size.y);
        ((GridData) button.getLayoutData()).heightHint = square;
        ((GridData) button.getLayoutData()).widthHint = square;
        return button;
    }

    /**
     * Create a predefined button with appearance to add an item.
     * 
     * @return
     */
    public Button createButtonPlus() {
        // Use TIME icon (X).
        Button button = createButton(FontAwesome.PLUS, SWT.FLAT);
        // Change the font (it's a bigger font).
        button.setFont(getIconFont(button));
        // Set the size of the button to be square
        Point size = button.computeSize(SWT.DEFAULT, SWT.DEFAULT);
        int square = Math.max(size.x, size.y);
        ((GridData) button.getLayoutData()).heightHint = square;
        ((GridData) button.getLayoutData()).widthHint = square;
        return button;
    }

    /**
     * Create switch buton.
     * 
     * @return
     */
    public SwitchButton createSwitchButton() {
        addColumn();
        SwitchButton button = new SwitchButton(this, SWT.NONE);
        button.setBackground(getBackground());
        button.setLayoutData(new GridData(SWT.RIGHT, SWT.CENTER, false, false));
        button.setEnabled(getEnabled());
        registerlisteners(button);
        return button;
    }

    /**
     * Return the widget background color.
     */
    @Override
    public Color getBackground() {
        return this.bg;
    }

    /**
     * Return the color used to draw help text.
     * 
     * @return the color or null if using default.
     */
    public Color getHelpTextForeground() {
        if (helpTextFg == null) {
            return getDisplay().getSystemColor(SWT.COLOR_WIDGET_NORMAL_SHADOW);
        }
        return helpTextFg;
    }

    /**
     * Return the color used has background when mouse is over the widget.
     * 
     * @return
     */
    private Color getOverBackground() {
        if (this.bgOver != null) {
            return this.bgOver;
        }
        RGB rgb = blend(new RGB(0, 0, 0), this.bg.getRGB(), 5);
        this.bgOver = new Color(getDisplay(), rgb);
        return this.bgOver;
    }

    /**
     * Return the widget text.
     * 
     * @return
     */
    public String getTitle() {
        checkWidget();
        return leftTitleLabel.getText();
    }

    /**
     * Return the help text.
     * 
     * @param text
     *            the help text.
     */
    public String getTitleHelpText(String text) {
        checkWidget();
        if (leftTitleHelpLabel != null) {
            return leftTitleHelpLabel.getText();
        }
        return null;
    }

    /**
     * Return the item value (show at the left)
     * 
     * @return the text value or null.
     */
    public String getValue() {
        checkWidget();
        if (rightValueText != null) {
            return rightValueText.getText();
        }
        return null;
    }

    /**
     * Return the help text value (show under the value at the left).
     * 
     * @return the help text or null.
     */
    public String getValueHelpText() {
        checkWidget();
        if (rightValueHelpText != null) {
            return rightValueHelpText.getText();
        }
        return null;
    }

    protected void onDispose() {
        if (this.bgOver != null) {
            this.bgOver.dispose();
        }
        this.bgOver = null;
    }

    private void registerlisteners(Control control) {
        control.addListener(SWT.MouseEnter, listener);
        control.addListener(SWT.MouseExit, listener);
    }

    /**
     * Set the widget color.
     */
    @Override
    public void setBackground(Color color) {
        if (color == null) {
            color = Display.getDefault().getSystemColor(SWT.COLOR_LIST_BACKGROUND);
        }
        this.bg = color;
        // Reset the bg over color.
        this.bgOver = null;
        if (getEnabled() && !over) {
            setBackgroundInternal(color);
        }
    }

    /**
     * Used internally to change the background color without changing the value return by getBackground();
     * 
     * @param color
     *            the new background color.
     */
    private void setBackgroundInternal(Color color) {
        super.setBackground(color);
        if (left != null) {
            left.setBackground(color);
        }
        if (right != null) {
            right.setBackground(color);
        }
        if (leftTitleLabel != null) {
            leftTitleLabel.setBackground(color);
        }
        if (leftTitleHelpLabel != null) {
            leftTitleHelpLabel.setBackground(color);
        }
        if (rightValueHelpText != null) {
            rightValueHelpText.setBackground(color);
        }
        if (rightValueText != null) {
            rightValueText.setBackground(color);
        }
    }

    /**
     * Enables the receiver if the argument is <code>true</code>, and disables it otherwise. A disabled control is
     * typically not selectable from the user interface and draws with an inactive or "grayed" look.
     */
    @Override
    public void setEnabled(boolean enabled) {
        super.setEnabled(enabled);
        if (leftTitleLabel != null) {
            leftTitleLabel.setEnabled(enabled);
        }
        if (leftTitleHelpLabel != null) {
            leftTitleHelpLabel.setEnabled(enabled);
        }
        if (rightValueHelpText != null) {
            rightValueHelpText.setEnabled(enabled);
        }
        if (rightValueText != null) {
            rightValueText.setEnabled(enabled);
        }
        // Change bg color.
        if (enabled) {
            setBackgroundInternal(getBackground());
        } else {
            setBackgroundInternal(getDisplay().getSystemColor(SWT.COLOR_WIDGET_BACKGROUND));
        }
    }

    /**
     * Sets the receiver's foreground color to the color specified by the argument, or to the default system color for
     * the control if the argument is null.
     */
    @Override
    public void setForeground(Color color) {
        super.setForeground(color);
        if (leftTitleLabel != null) {
            leftTitleLabel.setForeground(color);
        }
        if (rightValueText != null) {
            rightValueText.setForeground(color);
        }
    }

    /**
     * Sets the receiver's foreground color to the color specified by the argument, or to the default system color for
     * the control if the argument is null.
     * 
     * @param color
     *            the new color or null to use default.
     */
    public void setHelpTextForeground(Color color) {
        this.helpTextFg = color;
        if (rightValueHelpText != null) {
            rightValueHelpText.setForeground(getHelpTextForeground());
        }
        if (leftTitleHelpLabel != null) {
            leftTitleHelpLabel.setForeground(getHelpTextForeground());
        }
    }

    @Override
    public void setLayout(Layout layout) {
        // Do nothing.
    }

    /**
     * Set widget text.
     * 
     * @param text
     *            the new text.
     */
    public void setTitle(String text) {
        checkWidget();
        leftTitleLabel.setText(text);
        layout(true, true);
    }

    /**
     * Set the help text (placed under the title)
     * 
     * @param text
     */
    public void setTitleHelpText(String text) {
        checkWidget();
        if (text != null) {
            if (leftTitleHelpLabel == null) {
                leftTitleHelpLabel = new Label(left, SWT.NONE);
                leftTitleHelpLabel.setBackground(getBackground());
                leftTitleHelpLabel.setForeground(getHelpTextForeground());
                leftTitleHelpLabel.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
                leftTitleHelpLabel.setEnabled(getEnabled());
                registerlisteners(leftTitleHelpLabel);
            }
            leftTitleHelpLabel.setText(text);
            layout(true, true);
        } else {
            if (leftTitleHelpLabel != null) {
                leftTitleHelpLabel.dispose();
            }
        }

    }

    /**
     * Sets the receiver's tool tip text to the argument, which may be null indicating that the default tool tip for the
     * control will be shown.
     */
    public void setToolTipText(String string) {
        checkWidget();
        super.setToolTipText(string);
        if (leftTitleLabel != null) {
            leftTitleLabel.setToolTipText(string);
        }
        if (leftTitleHelpLabel != null) {
            leftTitleHelpLabel.setToolTipText(string);
        }
    }

    /**
     * Sets the item value (show at the left).
     * 
     * @param text
     *            the text value or null.
     */
    public void setValue(String text) {
        checkWidget();
        if (text != null) {
            if (rightValueText == null) {
                rightValueText = new Text(right, SWT.READ_ONLY);
                rightValueText.setBackground(getBackground());
                rightValueText.setLayoutData(new GridData(SWT.RIGHT, SWT.CENTER, false, false));
                rightValueText.setEnabled(getEnabled());
                rightValueText.setToolTipText(getToolTipText());
                registerlisteners(rightValueText);
            }
            rightValueText.setText(text);
            layout(true, true);
        } else {
            if (rightValueText != null) {
                rightValueText.dispose();
            }
        }
    }

    /**
     * Sets the help text for value (show under the value at the left).
     * 
     * @param text
     *            the help text or null.
     */
    public void setValueHelpText(String text) {
        checkWidget();
        if (text != null) {
            if (rightValueHelpText == null) {
                rightValueHelpText = new Text(right, SWT.READ_ONLY);
                rightValueHelpText.setBackground(getBackground());
                rightValueHelpText.setForeground(getHelpTextForeground());
                rightValueHelpText.setLayoutData(new GridData(SWT.RIGHT, SWT.CENTER, false, false));
                rightValueHelpText.setEnabled(getEnabled());
                registerlisteners(rightValueHelpText);
            }
            rightValueHelpText.setText(text);
            layout(true, true);
        } else {
            if (rightValueHelpText != null) {
                rightValueHelpText.dispose();
            }
        }
    }

}
