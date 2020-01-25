/*----------------------------------------------------------------------------*/
/* Copyright (c) 2017-2018 FIRST. All Rights Reserved.                        */
/* Open Source Software - may be modified and shared by FRC teams. The code   */
/* must be accompanied by the FIRST BSD license file in the root directory of */
/* the project.                                                               */
/*----------------------------------------------------------------------------*/

package frc.robot;

import edu.wpi.first.wpilibj.Joystick;
import edu.wpi.first.wpilibj.TimedRobot;
import edu.wpi.first.wpilibj.XboxController;
import edu.wpi.first.wpilibj.controller.PIDController;
import edu.wpi.first.wpilibj.smartdashboard.SendableChooser;
import edu.wpi.first.wpilibj.smartdashboard.SmartDashboard;
import com.ctre.phoenix.motorcontrol.ControlMode;
import com.ctre.phoenix.motorcontrol.can.TalonSRX;
import com.ctre.phoenix.motorcontrol.can.VictorSPX;

import java.util.List;

import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableEntry;
import edu.wpi.first.networktables.NetworkTableInstance;

/**
 * The VM is configured to automatically run this class, and to call the
 * functions corresponding to each mode, as described in the TimedRobot
 * documentation. If you change the name of this class or the package after
 * creating this project, you must also update the build.gradle file in the
 * project.
 */
public class Robot extends TimedRobot {
  private NetworkTableInstance inst;
  private NetworkTable table;
  private NetworkTableEntry xEntry;
  private NetworkTableEntry yEntry;
  private NetworkTableEntry pidP;
  private NetworkTableEntry pidI;
  private NetworkTableEntry pidD;
  private PIDController contr;

  private TalonSRX leftMotor1;
  private TalonSRX leftMotor2;
  
  private TalonSRX rightMotor1;
  private VictorSPX rightMotor2;

  private XboxController controller;
  /**
   * This function is run when the robot is first started up and should be
   * used for any initialization code.
   */
  @Override
  public void robotInit() {
    this.inst = NetworkTableInstance.getDefault();
    this.table = inst.getTable("SmartDashboard");
    this.xEntry = table.getEntry("tape-x");
    this.yEntry = table.getEntry("tape-y");
    this.pidP = table.getEntry("pid/p");
    this.pidI = table.getEntry("pid/i");
    this.pidD = table.getEntry("pid/d");
    this.pidP.setDouble(0.05);
    this.pidI.setDouble(0.00);
    this.pidD.setDouble(0.00);
    contr = new PIDController(0.05, 0, 0.02);
    contr.setSetpoint(0.0);
    leftMotor1 = new TalonSRX(0);
    leftMotor2 = new TalonSRX(1);
    rightMotor1 = new TalonSRX(2);
    rightMotor2 = new VictorSPX(3);
    //leftMotor2.follow(leftMotor1);
    rightMotor2.follow(rightMotor1);
    controller = new XboxController(0);
  }

  /**
   * This function is called every robot packet, no matter the mode. Use
   * this for items like diagnostics that you want ran during disabled,
   * autonomous, teleoperated and test.
   *
   * <p>This runs after the mode specific periodic functions, but before
   * LiveWindow and SmartDashboard integrated updating.
   */
  @Override
  public void robotPeriodic() {
  }

  /**
   * This autonomous (along with the chooser code above) shows how to select
   * between different autonomous modes using the dashboard. The sendable
   * chooser code works with the Java SmartDashboard. If you prefer the
   * LabVIEW Dashboard, remove all of the chooser code and uncomment the
   * getString line to get the auto name from the text box below the Gyro
   *
   * <p>You can add additional auto modes by adding additional comparisons to
   * the switch structure below with additional strings. If using the
   * SendableChooser make sure to add them to the chooser code above as well.
   */
  @Override
  public void autonomousInit() {
  }

  /**
   * This function is called periodically during autonomous.
   */
  @Override
  public void autonomousPeriodic() {
  }

  /**
   * This function is called periodically during operator control.
   */
  @Override
  public void teleopPeriodic() {
    
    if(xEntry.getValue().getDouble() < 0) {
      return;
    }
    contr.setPID(this.pidP.getValue().getDouble(), this.pidI.getValue().getDouble(), this.pidD.getValue().getDouble());
    double x = (xEntry.getValue().getDouble()-160.0);
    double motorPower = contr.calculate(x);
    leftMotor1.set(ControlMode.PercentOutput, motorPower);
    rightMotor1.set(ControlMode.PercentOutput, motorPower);
    
    /*
    double motorPower = controller.getRawAxis(1);
    System.out.println(motorPower);
    leftMotor1.set(ControlMode.PercentOutput, motorPower);
    rightMotor1.set(ControlMode.PercentOutput, motorPower*0.0);
    */
  }

  /**
   * This function is called periodically during test mode.
   */
  @Override
  public void testPeriodic() {
  }
}
