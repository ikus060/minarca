package com.patrikdufresne.minarca.ui;

import org.eclipse.swt.SWT;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.graphics.Rectangle;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Layout;

/**
 * Composite used to display CListItem. This widget is commonly used to show user settings.
 * 
 * @author Patrik Dufresne
 * 
 */
public class CList extends Composite {

    /**
     * Custom layout used by this widget.
     * 
     * @author Patrik Dufresne
     * 
     */
    private static class ColumnLayout extends Layout {

        // fixed margin and spacing
        public static final int MARGIN = 0;
        public static final int SPACING = 0;

        /** The maximum widget height */
        int maxWidth;
        /** The total height (sum of all height) */
        int totalHeight;
        /** The max item height */
        int maxItemHeight;
        /** Cache */
        Point[] sizes;

        /**
         * Compute the widget size.
         */
        protected Point computeSize(Composite composite, int wHint, int hHint, boolean flushCache) {
            Control children[] = composite.getChildren();
            if (flushCache || sizes == null || sizes.length != children.length) {
                initialize(children);
            }
            int width = wHint, height = hHint;
            if (wHint == SWT.DEFAULT) width = maxWidth;
            if (hHint == SWT.DEFAULT) height = totalHeight;
            return new Point(width + 2 * MARGIN, height + 2 * MARGIN);
        }

        void initialize(Control children[]) {
            // Determine the item height
            maxItemHeight = 0;
            maxWidth = 0;
            sizes = new Point[children.length];
            for (int i = 0; i < children.length; i++) {
                sizes[i] = children[i].computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
                if (children[i] instanceof CListItem) {
                    maxItemHeight = Math.max(maxItemHeight, sizes[i].y);
                }
                maxWidth = Math.max(maxWidth, sizes[i].x);
            }
            // Compute the total height.
            totalHeight = 0;
            for (int i = 0; i < children.length; i++) {
                sizes[i] = children[i].computeSize(SWT.DEFAULT, SWT.DEFAULT, true);
                if (children[i] instanceof CListItem) {
                    totalHeight += maxItemHeight;
                } else {
                    totalHeight += sizes[i].y;
                }
            }
            totalHeight += (children.length - 1) * SPACING;
        }

        protected void layout(Composite composite, boolean flushCache) {
            Control children[] = composite.getChildren();
            if (flushCache || sizes == null || sizes.length != children.length) {
                initialize(children);
            }
            Rectangle rect = composite.getClientArea();
            int x = MARGIN, y = MARGIN;
            int width = Math.max(rect.width - 2 * MARGIN, maxWidth);
            for (int i = 0; i < children.length; i++) {
                int height;
                if (children[i] instanceof CListItem) {
                    height = maxItemHeight;
                } else {
                    height = sizes[i].y;
                }
                children[i].setBounds(x, y, width, height);
                y += height + SPACING;
            }
        }
    }

    /**
     * Create a custom list.
     * 
     * @param parent
     *            The composite parent
     * 
     * @param style
     *            the style usually SWT.NONE)
     */
    public CList(Composite parent, int style) {
        super(parent, style);

        // Set a custom layout.
        super.setLayout(new ColumnLayout());

        // Set default background color.
        setBackground(Display.getDefault().getSystemColor(SWT.COLOR_LIST_BACKGROUND));
    }

    /**
     * This implementation doesn't change the layout.
     */
    @Override
    public void setLayout(Layout layout) {
        // Do nothing.
    }

}
