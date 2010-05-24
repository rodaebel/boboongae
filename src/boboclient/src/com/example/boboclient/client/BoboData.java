package com.example.boboclient.client;

import com.google.gwt.core.client.JavaScriptObject;

public class BoboData extends JavaScriptObject {

	protected BoboData() {}

	public final native String getString() /*-{ return this.string; }-*/;
}
