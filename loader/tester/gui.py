from pathlib import Path
import wx


class MainFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.button = wx.Button(panel, label="Zip dosyası seç")
        sizer.Add(self.button, 0, wx.ALL | wx.CENTER, 5)

        panel.SetSizer(sizer)

        self.Bind(wx.EVT_BUTTON, self.on_button_click, self.button)

    def on_button_click(self, event):
        fd = wx.FileDialog(
            self,
            "Arşiv dosyası seç",
            wildcard="Arşiv dosyaları (*.7z;*.xz;*.bz2;*.gz;*.tar;*.zip;*.wim)|*.7z;*.xz;*.bz2;*.gz;*.tar;*.zip;*.wim",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        with fd as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            path = fileDialog.GetPath()
            path = Path(path)
            print(path)


class TesterApp(wx.App):
    def OnInit(self):
        frame = MainFrame(None, title="Robo-Core Tester")
        frame.Show(True)
        return True


if __name__ == "__main__":
    app = TesterApp()
    app.MainLoop()
