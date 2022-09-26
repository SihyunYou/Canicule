using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Diagnostics;
using System.IO;
using System.Management;

namespace ChatEtChien
{
    public partial class Form1 : Form
    {
        bool EstFini = false;
        Process Trader;

        public Form1()
        {
            if (File.Exists("log/etat.txt"))
            {
                File.Delete("log/etat.txt");
            }

            if (File.Exists("log/masse.txt"))
            {
                File.Delete("log/masse.txt");
            }

            Thread t = new Thread(Lire);
            t.Start();

            Trader = new Process();

            Trader.StartInfo.FileName = "trader.exe";
            Trader.StartInfo.CreateNoWindow = true;
            Trader.StartInfo.Arguments = "-c True";

            Trader.Start();
            InitializeComponent();
        }

        int Premier = 0;
        int Dernier = 0;
        int Operation = 1;

        private void Lire()
        {
            while (!EstFini)
            {
                try
                {
                    if (File.Exists("log/etat.txt"))
                    {
                        StreamReader sr = new StreamReader("log/etat.txt");
                        string s = sr.ReadLine();
                        sr.Close();

                        Operation = Convert.ToInt32(s[1].ToString());

                        switch (Operation)
                        {
                            case 1:
                                button2.Text = "프로그램을 구성 중이에요.";
                                button2.ForeColor = SystemColors.ControlText;
                                break;
                            case 2:
                                button2.Text = "서버에서 데이터를 받아오고 있어요.";
                                button2.ForeColor = SystemColors.ControlText;
                                break;
                            case 3:
                                button2.Text = "코인들을 모니터링하고 있어요.";
                                button2.ForeColor = SystemColors.ControlText;
                                pictureBox2.SendToBack();
                                break;
                            case 4:
                                button2.Text = "\'" + s.Split(',')[1] + "\'를 매수할게요!";
                                button2.ForeColor = SystemColors.ControlText;
                                pictureBox1.SendToBack();
                                break;
                            case 5:
                                button2.Text = "\'" + s.Split(',')[1] + "\'에 투자하고 있어요.";
                                button2.ForeColor = SystemColors.ControlText;
                                break;
                            case 6:
                                button2.Text = "매수에 실패했어요...";
                                button2.ForeColor = Color.OrangeRed;
                                break;
                            case 7:
                                button2.Text = "매도 성공!";
                                button2.ForeColor = Color.LimeGreen;
                                break;
                            case 0:
                                button2.ForeColor = Color.OrangeRed;
                                button2.Text = "오류가 났어요...";
                                break;
                        }
                    }

                    if (File.Exists("log/masse.txt"))
                    {
                        StreamReader sr = new StreamReader("log/masse.txt");
                        string[] s = sr.ReadLine().Split(',');
                        sr.Close();

                        Premier = Convert.ToInt32(s[0]);
                        Dernier = Convert.ToInt32(s[1]);
                        int t = Premier - Dernier;
                        string p = "";

                        if (t > 0)
                        {
                            p += "+";
                        }
                        p += String.Format("{0:#,0}", t) + "\\ (";
                        if (t > 0)
                        {
                            p += "+";
                            button3.ForeColor = Color.LimeGreen;
                        }
                        else if (t < 0)
                        {
                            p += "-";
                            button3.ForeColor = Color.OrangeRed;
                        }
                        else
                        {
                            button3.ForeColor = SystemColors.ControlText;
                        }

                        string q = Math.Round(Math.Abs(t) / (double)Dernier * 100, 3).ToString();
                        if ("0" == q)
                        {
                            q = "0.000";
                        }
                        p += q;
                        p += "%)";

                        button3.Text = p;
                        button4.Text = String.Format("{0:#,0}", Dernier) + "\\";
                    }
                }
                catch(Exception)
                {

                }

                Thread.Sleep(100);
            }
        }

        private static void KillProcessAndChildrens(int pid)
        {
            ManagementObjectSearcher processSearcher = new ManagementObjectSearcher
              ("Select * From Win32_Process Where ParentProcessID=" + pid);
            ManagementObjectCollection processCollection = processSearcher.Get();

            try
            {
                Process proc = Process.GetProcessById(pid);
                if (!proc.HasExited) proc.Kill();
            }
            catch (ArgumentException)
            {
                // Process already exited.
            }

            if (processCollection != null)
            {
                foreach (ManagementObject mo in processCollection)
                {
                    KillProcessAndChildrens(Convert.ToInt32(mo["ProcessID"])); //kill child processes(also kills childrens of childrens etc.)
                }
            }
        }

        private void Form1_FormClosed(object sender, FormClosedEventArgs e)
        {
            EstFini = true;
            KillProcessAndChildrens(Trader.Id);
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            switch (Operation)
            {
                case 4:
                case 5:
                case 6:
                case 7:
                    var result = MessageBox.Show("투자가 진행중입니다. 정말 종료하시겠습니까?", "멍?", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                    if (result == DialogResult.No)
                    {
                        e.Cancel = true;
                    }
                    break;
            }
        }
    }
}
