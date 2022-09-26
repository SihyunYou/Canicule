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

namespace ChatEtChien
{
    public partial class Form1 : Form
    {
        bool EstFini = false;
        Thread t;

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

            t = new Thread(Lire);
            t.Start();
            
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
                    StreamReader sr = new StreamReader("log/etat.txt");
                    string s = sr.ReadLine();
                    sr.Close();

                    Operation = Convert.ToInt32(s[1]);
                    switch(Operation)
                    {
                        case 1:
                            button2.Text = "대기 중";
                            button2.ForeColor = SystemColors.ControlText;
                            break;
                        case 2:
                            button2.Text = "초기화 중";
                            button2.ForeColor = SystemColors.ControlText;
                            break;
                        case 3:
                            button2.Text = "모니터링 중";
                            button2.ForeColor = SystemColors.ControlText;
                            break;
                        case 4:
                            button2.Text = "매수주문 요청 중 (" + s.Split(',')[1] + ")";
                            button2.ForeColor = SystemColors.ControlText;
                            break;
                        case 5:
                            button2.Text = "투자 중 (" + s.Split(',')[1] + ")";
                            button2.ForeColor = SystemColors.ControlText;
                            break;
                        case 6:
                            button2.Text = "실패 (시간초과)";
                            button2.ForeColor = Color.OrangeRed;
                            break;
                        case 7:
                            button2.Text = "매도 성공!";
                            button2.ForeColor = Color.LimeGreen;
                            break;
                        case 0:
                        default:
                            button2.ForeColor = Color.OrangeRed;
                            button2.Text = "프로그램 죽음 ㅠ";
                            break;
                    }
                }
                catch(Exception)
                {

                }

                try
                {
                    StreamReader sr = new StreamReader("log/masse.txt");
                    string[] s = sr.ReadLine().Split(',');
                    sr.Close();

                    Premier = Convert.ToInt32(s[0]);
                    Dernier = Convert.ToInt32(s[1]);
                    int t = Premier - Dernier;

                    string p = t.ToString() + "\\ (";
                    if (t > 0)
                    {
                        p += "+";
                        button3.ForeColor = Color.OrangeRed;
                    }
                    else if(t < 0)
                    {
                        p += "-";
                        button3.ForeColor = Color.LimeGreen;
                    }
                    else
                    {
                        button3.ForeColor = SystemColors.ControlText;
                    }

                    string q = Math.Round(Math.Abs(t) / (double)Dernier * 100, 3).ToString();
                    if("0" == q)
                    {
                        q = "0.000";
                    }
                    p += "%)";

                    button3.Text = String.Format("{0:#,0}", p);
                    button4.Text = String.Format("{0:#,0}", Dernier) + "\\"; 
                }
                catch (Exception)
                {

                }

                Thread.Sleep(100);
            }
        }


        private void button1_Click(object sender, EventArgs e)
        {
            button1.SendToBack();
            Process.Start("cmd.exe", "/C trader.py");
        }

        private void Form1_FormClosed(object sender, FormClosedEventArgs e)
        {
            EstFini = true;
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            switch(Operation)
            {
                case 4:
                case 5:
                case 6:
                case 7:
                    var result = MessageBox.Show("냥?", "현재 상태에서 종료하실 수 없습니다.\n잠시 기다려주세요.", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                    if (result == DialogResult.No)
                    {
                        e.Cancel = true;
                    }
                    else
                    {
                        Application.Exit();
                    }
                    break;
            }
        }
    }
}
