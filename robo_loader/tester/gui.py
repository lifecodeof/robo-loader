from multiprocessing import Process
from pathlib import Path
import wx
import wx.adv

from robo_loader.tester.test_module import test_module


class MainFrame(wx.Frame):
    process: Process | None = None

    def __init__(self, *args, auto_pick_file: str | None = None, **kw):
        super(MainFrame, self).__init__(*args, **kw)

        self.CreateStatusBar()
        self.SetStatusText("Hazır")

        panel = wx.Panel(self)
        self.h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.v_sizer = wx.BoxSizer(wx.VERTICAL)

        self.h_sizer.Add(self.v_sizer, 1, wx.CENTER)

        self.b_file_select = wx.Button(panel, label="Zip dosyası seç")
        self.v_sizer.Add(self.b_file_select, 0, wx.ALL | wx.CENTER, 5)

        self.b_stop = wx.Button(panel, label="Durdur")
        self.b_stop.Disable()
        self.v_sizer.Add(self.b_stop, 0, wx.ALL | wx.CENTER, 5)

        self.hl_link = wx.adv.HyperlinkCtrl(
            panel, label="http://localhost:8000", url="http://localhost:8000"
        )
        self.v_sizer.Add(self.hl_link, 0, wx.ALL | wx.CENTER, 5)
        self.hl_link.Hide()

        panel.SetSizer(self.h_sizer)

        self.Bind(wx.EVT_BUTTON, self.on_b_file_select_click, self.b_file_select)
        self.Bind(wx.EVT_BUTTON, self.on_b_stop_click, self.b_stop)

        if auto_pick_file:
            self.on_file_selected(Path(auto_pick_file))

    def on_b_file_select_click(self, event):
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
            self.on_file_selected(path)

    def on_b_stop_click(self, event):
        self.stop_thread()

    def on_file_selected(self, path: Path):
        self.start_thread(path)

    def start_thread(self, path: Path):
        if self.process:
            self.process.terminate()

        process = Process(target=test_module, args=(path,), daemon=True)
        process.start()
        self.process = process
        self.b_file_select.Disable()
        self.b_stop.Enable()
        self.hl_link.Show()
        self.v_sizer.Layout()
        self.h_sizer.Layout()
        self.SetStatusText("Çalışıyor - loglar için terminali kontrol edin")

    def stop_thread(self):
        if self.process:
            self.process.terminate()
        self.b_file_select.Enable()
        self.b_stop.Disable()
        self.hl_link.Hide()
        self.SetStatusText("Hazır")


class TesterApp(wx.App):
    auto_pick_file: str | None = None

    def __init__(self, auto_pick_file: str | None = None):
        self.auto_pick_file = auto_pick_file
        super().__init__()

    def OnInit(self):
        frame = MainFrame(
            None, title="Robo-Core Tester", auto_pick_file=self.auto_pick_file
        )
        frame.Show(True)
        return True


if __name__ == "__main__":
    app = TesterApp()
    app.MainLoop()
